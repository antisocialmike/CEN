from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from psycopg2 import errors as psycopg2_errors

from server.src.main import app
from server.src.middlewares.auth_middleware import (
    create_access_token,
    verify_password,
)
from server.src.repositories.company_repository import NotFoundError

client = TestClient(app)

OWNER_ID = 20
MINE = 1
FOREIGN = 2
REPOSITORY = "server.src.routes.owner_routes.company_repository"
CONTEXT = "server.src.middlewares.company_context.company_repository"


def _headers(role: str = "owner", employee_id: int = OWNER_ID) -> dict:
    token = create_access_token(data={
        "sub": role + "@cen.com", "role": role, "employee_id": employee_id,
    })
    return {"Authorization": f"Bearer {token}"}


OWNER = _headers()

COMPANY = {
    "id": MINE, "legal_name": "Grupo Norte SA de CV", "trade_name": None,
    "rfc": "GNO010101AB1", "registro_patronal": None,
    "entidad_federativa": "NLE", "is_active": True,
    "created_at": datetime(2026, 9, 23, tzinfo=timezone.utc),
    "admins": [{
        "id": 3, "name": "Fernanda Rios", "email": "fer@norte.mx",
        "is_active": True, "assigned_at": "2026-09-23T10:00:00+00:00",
    }],
}


@pytest.fixture(autouse=True)
def owns_only_company_1():
    with patch(CONTEXT) as context:
        context.owner_has_company.side_effect = (
            lambda owner_id, company_id:
            owner_id == OWNER_ID and company_id == MINE
        )
        yield context


@pytest.fixture
def repository():
    with patch(REPOSITORY) as mock:
        mock.get_owner_company.return_value = COMPANY
        yield mock


@pytest.mark.parametrize("role", ["superadmin", "admin", "employee"])
@pytest.mark.parametrize("method, path", [
    ("get", "/owner/companies"),
    ("put", f"/owner/companies/{MINE}"),
    ("post", f"/owner/companies/{MINE}/deactivate"),
    ("post", f"/owner/companies/{MINE}/admins/invite"),
    ("post", f"/owner/companies/{MINE}/admins"),
    ("delete", f"/owner/companies/{MINE}/admins/3"),
])
def test_only_owners_manage_companies(role, method, path):
    response = client.request(method, path, headers=_headers(role))

    assert response.status_code == 403


def test_list_my_companies(repository):
    repository.list_owner_companies.return_value = [COMPANY]

    response = client.get("/owner/companies", headers=OWNER)

    assert response.status_code == 200
    assert response.json()[0]["admins"][0]["email"] == "fer@norte.mx"
    repository.list_owner_companies.assert_called_once_with(OWNER_ID)


@pytest.mark.parametrize("method, path, body", [
    ("get", f"/owner/companies/{FOREIGN}", None),
    ("put", f"/owner/companies/{FOREIGN}", {"legal_name": "Ajena"}),
    ("post", f"/owner/companies/{FOREIGN}/deactivate", None),
    ("post", f"/owner/companies/{FOREIGN}/activate", None),
    ("post", f"/owner/companies/{FOREIGN}/admins/invite",
     {"name": "X", "email": "x@ajena.mx"}),
    ("post", f"/owner/companies/{FOREIGN}/admins", {"email": "x@ajena.mx"}),
    ("delete", f"/owner/companies/{FOREIGN}/admins/3", None),
])
def test_a_company_of_somebody_else_does_not_exist(
    repository, method, path, body
):
    response = client.request(method, path, json=body, headers=OWNER)

    assert response.status_code == 404
    assert repository.method_calls == []


def test_update_my_company(repository):
    response = client.put(
        f"/owner/companies/{MINE}",
        json={"legal_name": "Grupo Norte SA de CV", "rfc": "gno010101ab1"},
        headers=OWNER,
    )

    assert response.status_code == 200
    company_id, data, actor_id = repository.update_company.call_args[0]
    assert (company_id, actor_id) == (MINE, OWNER_ID)
    assert data["rfc"] == "GNO010101AB1"


def test_update_rejects_a_malformed_rfc(repository):
    response = client.put(
        f"/owner/companies/{MINE}",
        json={"legal_name": "Grupo Norte", "rfc": "NO-ES-RFC"},
        headers=OWNER,
    )

    assert response.status_code == 422
    repository.update_company.assert_not_called()


@pytest.mark.parametrize("action, active", [
    ("deactivate", False), ("activate", True),
])
def test_toggle_my_company(repository, action, active):
    response = client.post(
        f"/owner/companies/{MINE}/{action}", headers=OWNER
    )

    assert response.status_code == 200
    repository.set_company_active.assert_called_once_with(
        MINE, active, OWNER_ID
    )


def test_invite_an_admin(repository):
    repository.invite_admin.return_value = 31

    response = client.post(
        f"/owner/companies/{MINE}/admins/invite",
        json={"name": "Pablo Soto", "email": "pablo@norte.mx"},
        headers=OWNER,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["admin_id"] == 31
    company_id, data, actor_id = repository.invite_admin.call_args[0]
    assert (company_id, actor_id) == (MINE, OWNER_ID)
    assert verify_password(body["temporary_password"], data["password_hash"])


def test_invite_an_admin_with_a_taken_email(repository):
    repository.invite_admin.side_effect = psycopg2_errors.UniqueViolation()

    response = client.post(
        f"/owner/companies/{MINE}/admins/invite",
        json={"name": "Pablo Soto", "email": "pablo@norte.mx"},
        headers=OWNER,
    )

    assert response.status_code == 409


def test_assign_an_existing_admin_by_email(repository):
    response = client.post(
        f"/owner/companies/{MINE}/admins",
        json={"email": "fer@norte.mx"},
        headers=OWNER,
    )

    assert response.status_code == 200
    repository.assign_admin_by_email.assert_called_once_with(
        MINE, "fer@norte.mx", OWNER_ID
    )


def test_assign_an_unknown_admin(repository):
    repository.assign_admin_by_email.side_effect = NotFoundError()

    response = client.post(
        f"/owner/companies/{MINE}/admins",
        json={"email": "empleado@norte.mx"},
        headers=OWNER,
    )

    assert response.status_code == 404
    assert "administrador" in response.json()["detail"]


def test_unassign_an_admin(repository):
    response = client.delete(
        f"/owner/companies/{MINE}/admins/3", headers=OWNER
    )

    assert response.status_code == 200
    repository.unassign_admin.assert_called_once_with(MINE, 3, OWNER_ID)


def test_unassign_somebody_who_is_not_an_admin_here(repository):
    repository.unassign_admin.side_effect = NotFoundError()

    response = client.delete(
        f"/owner/companies/{MINE}/admins/99", headers=OWNER
    )

    assert response.status_code == 404
