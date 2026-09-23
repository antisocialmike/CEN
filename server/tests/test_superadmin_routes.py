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
from server.src.repositories.company_repository import (
    NotFoundError,
    OrphanedCompanyError,
)

client = TestClient(app)

REPOSITORY = "server.src.routes.superadmin_routes.company_repository"


def _headers(role: str, employee_id: int = 1) -> dict:
    token = create_access_token(data={
        "sub": role + "@cen.com", "role": role, "employee_id": employee_id,
    })
    return {"Authorization": f"Bearer {token}"}


SUPERADMIN = _headers("superadmin", 99)

OWNER = {
    "id": 5, "name": "Laura Mendez", "email": "laura@grupo.mx",
    "is_active": True,
    "companies": [{"id": 1, "legal_name": "Grupo Norte", "is_active": True}],
}

COMPANY = {
    "id": 1, "legal_name": "Grupo Norte SA de CV", "trade_name": "Norte",
    "rfc": "GNO010101AB1", "registro_patronal": None,
    "entidad_federativa": "NLE", "is_active": True,
    "created_at": datetime(2026, 9, 23, tzinfo=timezone.utc),
    "owners": [{"id": 5, "name": "Laura Mendez", "is_active": True}],
}


@pytest.mark.parametrize("role", ["admin", "owner", "employee"])
@pytest.mark.parametrize("method, path", [
    ("get", "/superadmin/owners"),
    ("post", "/superadmin/owners"),
    ("post", "/superadmin/owners/5/deactivate"),
    ("get", "/superadmin/companies"),
    ("post", "/superadmin/companies"),
    ("delete", "/superadmin/companies/1/owners/5"),
])
def test_only_the_superadmin_reaches_the_platform(role, method, path):
    response = client.request(method, path, headers=_headers(role))

    assert response.status_code == 403


def test_the_platform_requires_authentication():
    assert client.get("/superadmin/owners").status_code == 401


@pytest.mark.parametrize("path", [
    "/employees", "/payroll/receipts",
])
def test_the_superadmin_does_not_see_payroll(path):
    response = client.get(path, headers=SUPERADMIN)

    assert response.status_code == 403


@patch(REPOSITORY + ".list_owners")
def test_list_owners(mock_list):
    mock_list.return_value = [OWNER]

    response = client.get("/superadmin/owners", headers=SUPERADMIN)

    assert response.status_code == 200
    assert response.json()[0]["companies"][0]["legal_name"] == "Grupo Norte"


@patch(REPOSITORY + ".get_owner")
@patch(REPOSITORY + ".create_owner")
def test_create_owner_returns_a_temporary_password(mock_create, mock_get):
    mock_create.return_value = 5
    mock_get.return_value = dict(OWNER, companies=[])

    response = client.post(
        "/superadmin/owners",
        json={"name": "Laura Mendez", "email": "laura@grupo.mx"},
        headers=SUPERADMIN,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["owner"]["id"] == 5
    stored, actor_id = mock_create.call_args[0]
    assert actor_id == 99
    assert verify_password(body["temporary_password"], stored["password_hash"])
    assert "password_hash" not in body["owner"]


@patch(REPOSITORY + ".create_owner")
def test_create_owner_with_a_taken_email(mock_create):
    mock_create.side_effect = psycopg2_errors.UniqueViolation()

    response = client.post(
        "/superadmin/owners",
        json={"name": "Laura Mendez", "email": "laura@grupo.mx"},
        headers=SUPERADMIN,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "El correo ya esta registrado"


@patch(REPOSITORY + ".update_owner")
def test_update_a_missing_owner(mock_update):
    mock_update.side_effect = NotFoundError()

    response = client.put(
        "/superadmin/owners/999",
        json={"name": "Nadie", "email": "nadie@grupo.mx"},
        headers=SUPERADMIN,
    )

    assert response.status_code == 404


@patch(REPOSITORY + ".set_owner_active")
def test_deactivate_the_last_owner_of_a_company(mock_set_active):
    mock_set_active.side_effect = OrphanedCompanyError(
        [{"id": 1, "legal_name": "Grupo Norte"}]
    )

    response = client.post(
        "/superadmin/owners/5/deactivate", headers=SUPERADMIN
    )

    assert response.status_code == 409
    assert "Grupo Norte" in response.json()["detail"]


@patch(REPOSITORY + ".get_owner")
@patch(REPOSITORY + ".set_owner_active")
def test_deactivate_owner(mock_set_active, mock_get):
    mock_get.return_value = dict(OWNER, is_active=False)

    response = client.post(
        "/superadmin/owners/5/deactivate", headers=SUPERADMIN
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    mock_set_active.assert_called_once_with(5, False, 99)


@patch(REPOSITORY + ".reset_owner_password")
def test_reset_owner_password(mock_reset):
    mock_reset.return_value = {
        "id": 5, "name": "Laura Mendez", "email": "laura@grupo.mx"
    }

    response = client.post(
        "/superadmin/owners/5/reset-password", headers=SUPERADMIN
    )

    assert response.status_code == 200
    body = response.json()
    assert body["owner_id"] == 5
    assert verify_password(
        body["temporary_password"], mock_reset.call_args[0][1]
    )


@patch(REPOSITORY + ".get_company")
@patch(REPOSITORY + ".create_company")
def test_create_company_normalizes_its_data(mock_create, mock_get):
    mock_create.return_value = 1
    mock_get.return_value = COMPANY

    response = client.post(
        "/superadmin/companies",
        json={
            "legal_name": "Grupo Norte SA de CV",
            "trade_name": "  ",
            "rfc": " gno010101ab1 ",
            "registro_patronal": "",
            "entidad_federativa": "NLE",
            "owner_id": 5,
        },
        headers=SUPERADMIN,
    )

    assert response.status_code == 201
    data, owner_id, actor_id = mock_create.call_args[0]
    assert data["rfc"] == "GNO010101AB1"
    assert data["trade_name"] is None
    assert data["registro_patronal"] is None
    assert "owner_id" not in data
    assert (owner_id, actor_id) == (5, 99)


@pytest.mark.parametrize("field, value", [
    ("rfc", "NO-ES-RFC"),
    ("registro_patronal", "12345"),
    ("entidad_federativa", "XX"),
])
def test_create_company_rejects_malformed_fields(field, value):
    payload = {"legal_name": "Grupo Norte", "owner_id": 5, field: value}

    response = client.post(
        "/superadmin/companies", json=payload, headers=SUPERADMIN
    )

    assert response.status_code == 422


def test_create_company_requires_an_owner():
    response = client.post(
        "/superadmin/companies",
        json={"legal_name": "Grupo Norte"},
        headers=SUPERADMIN,
    )

    assert response.status_code == 422


@patch(REPOSITORY + ".create_company")
def test_create_company_with_a_missing_owner(mock_create):
    mock_create.side_effect = NotFoundError()

    response = client.post(
        "/superadmin/companies",
        json={"legal_name": "Grupo Norte", "owner_id": 404},
        headers=SUPERADMIN,
    )

    assert response.status_code == 404


class _RfcTaken(psycopg2_errors.UniqueViolation):
    @property
    def diag(self):
        return type("Diag", (), {"constraint_name": "companies_rfc_key"})()


@patch(REPOSITORY + ".create_company")
def test_create_company_with_a_taken_rfc(mock_create):
    mock_create.side_effect = _RfcTaken()

    response = client.post(
        "/superadmin/companies",
        json={"legal_name": "Grupo Norte", "rfc": "GNO010101AB1",
              "owner_id": 5},
        headers=SUPERADMIN,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "El RFC ya esta registrado"


@patch(REPOSITORY + ".get_company")
@patch(REPOSITORY + ".assign_owner")
def test_assign_owner(mock_assign, mock_get):
    mock_get.return_value = COMPANY

    response = client.post(
        "/superadmin/companies/1/owners",
        json={"owner_id": 5},
        headers=SUPERADMIN,
    )

    assert response.status_code == 200
    mock_assign.assert_called_once_with(1, 5, 99)


@patch(REPOSITORY + ".unassign_owner")
def test_unassign_the_last_owner(mock_unassign):
    mock_unassign.side_effect = OrphanedCompanyError(
        [{"id": 1, "legal_name": "Grupo Norte"}]
    )

    response = client.delete(
        "/superadmin/companies/1/owners/5", headers=SUPERADMIN
    )

    assert response.status_code == 409


@patch(REPOSITORY + ".unassign_owner")
def test_unassign_an_owner_that_was_not_assigned(mock_unassign):
    mock_unassign.side_effect = NotFoundError()

    response = client.delete(
        "/superadmin/companies/1/owners/7", headers=SUPERADMIN
    )

    assert response.status_code == 404
