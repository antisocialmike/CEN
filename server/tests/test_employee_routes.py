from datetime import date
from unittest.mock import patch

import pytest
from psycopg2 import errors as psycopg2_errors
from fastapi.testclient import TestClient

from server.src.main import app
from server.src.middlewares.auth_middleware import create_access_token

client = TestClient(app)

ADMIN_COMPANY_ID = 1


@pytest.fixture(autouse=True)
def admin_company():
    # El admin de estas pruebas administra una sola empresa, la 1. Las
    # pruebas de aislamiento entre empresas viven en test_company_isolation.
    with patch(
        "server.src.middlewares.company_context.company_repository"
    ) as repository:
        repository.admin_company_ids.return_value = [ADMIN_COMPANY_ID]
        repository.admin_has_company.return_value = True
        yield repository


@pytest.fixture(autouse=True)
def email_lookup():
    with patch(
        "server.src.routes.employee_routes.payroll_repository.get_employee_by_email"
    ) as lookup:
        lookup.return_value = None
        yield lookup


def _admin_token():
    return create_access_token(
        data={"sub": "admin1", "role": "admin", "employee_id": 99}
    )


def _employee_token():
    return create_access_token(
        data={"sub": "empleado1", "role": "employee", "employee_id": 50}
    )


@patch("server.src.routes.employee_routes.payroll_repository.list_employees")
def test_list_employees_success(mock_list_employees):
    mock_list_employees.return_value = [
        {
            "id": 1, "name": "Ana Lopez", "email": "ana@cen.com",
            "role": "employee", "base_salary": 9000
        },
        {
            "id": 2, "name": "Luis Diaz", "email": "luis@cen.com",
            "role": "admin", "base_salary": 15000
        }
    ]

    response = client.get(
        "/employees",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["name"] == "Ana Lopez"


@patch("server.src.routes.employee_routes.payroll_repository.list_employees")
@patch("server.src.routes.employee_routes.payroll_repository.page_employees")
def test_list_employees_by_page(mock_page_employees, mock_list_employees):
    mock_page_employees.return_value = ([
        {
            "id": 21, "name": "Ana Lopez", "email": "ana@cen.com",
            "role": "employee", "base_salary": 9000
        }
    ], 21)

    response = client.get(
        "/employees?page=2",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["name"] == "Ana Lopez"
    assert (body["total"], body["page"], body["page_size"]) == (21, 2, 20)
    mock_page_employees.assert_called_once_with(ADMIN_COMPANY_ID, 20, 20)
    mock_list_employees.assert_not_called()


@pytest.mark.parametrize("query", ["page=0", "page_size=101"])
def test_list_employees_rejects_impossible_pages(query):
    response = client.get(
        "/employees?" + query,
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 422


def test_list_employees_requires_admin_role():
    response = client.get(
        "/employees",
        headers={"Authorization": f"Bearer {_employee_token()}"}
    )

    assert response.status_code == 403


def test_list_employees_requires_authentication():
    response = client.get("/employees")

    assert response.status_code == 401


@patch("server.src.routes.employee_routes.payroll_repository.create_employee")
def test_create_employee_success(mock_create_employee):
    mock_create_employee.return_value = 10

    response = client.post(
        "/employees",
        json={
            "name": "Juan Perez",
            "email": "juan@cen.com",
            "role": "employee",
            "base_salary": 12000,
            "password": "clave123"
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 10
    assert body["email"] == "juan@cen.com"
    assert "password" not in body
    assert "password_hash" not in body
    mock_create_employee.assert_called_once()


@patch("server.src.routes.employee_routes.payroll_repository.create_employee")
def test_create_employee_duplicate_email(mock_create_employee):
    mock_create_employee.side_effect = psycopg2_errors.UniqueViolation()

    response = client.post(
        "/employees",
        json={
            "name": "Juan Perez",
            "email": "juan@cen.com",
            "role": "employee",
            "base_salary": 12000,
            "password": "clave123"
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 409


def test_create_employee_requires_admin_role():
    response = client.post(
        "/employees",
        json={
            "name": "Juan Perez",
            "email": "juan@cen.com",
            "role": "employee",
            "base_salary": 12000,
            "password": "clave123"
        },
        headers={"Authorization": f"Bearer {_employee_token()}"}
    )

    assert response.status_code == 403


def test_create_employee_requires_authentication():
    response = client.post(
        "/employees",
        json={
            "name": "Juan Perez",
            "email": "juan@cen.com",
            "role": "employee",
            "base_salary": 12000,
            "password": "clave123"
        }
    )

    assert response.status_code == 401


def _admin_token_with_id(employee_id=1):
    return create_access_token(
        data={"sub": "admin1", "role": "admin", "employee_id": employee_id}
    )


def _updated_payload():
    return {
        "name": "Ana Lopez",
        "email": "ana@cen.com",
        "role": "employee",
        "base_salary": 19000
    }


@patch("server.src.routes.employee_routes.payroll_repository.update_employee")
def test_update_employee_success(mock_update):
    mock_update.return_value = {
        "id": 3, "name": "Ana Lopez", "email": "ana@cen.com",
        "role": "employee", "base_salary": 19000, "is_active": True
    }

    response = client.put(
        "/employees/3",
        json=_updated_payload(),
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    assert response.json()["base_salary"] == 19000
    assert mock_update.call_args[0][0] == 3


@patch("server.src.routes.employee_routes.payroll_repository.update_employee")
def test_update_employee_not_found(mock_update):
    mock_update.return_value = None

    response = client.put(
        "/employees/999",
        json=_updated_payload(),
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 404


@patch("server.src.routes.employee_routes.payroll_repository.update_employee")
def test_update_employee_cannot_drop_your_own_admin_role(mock_update):
    response = client.put(
        "/employees/1",
        json=_updated_payload(),
        headers={"Authorization": f"Bearer {_admin_token_with_id(1)}"}
    )

    assert response.status_code == 400
    mock_update.assert_not_called()


@patch("server.src.routes.employee_routes.payroll_repository.update_employee")
def test_update_employee_can_keep_your_own_admin_role(mock_update):
    mock_update.return_value = {
        "id": 1, "name": "Admin", "email": "admin@cen.com",
        "role": "admin", "base_salary": 20000, "is_active": True
    }

    response = client.put(
        "/employees/1",
        json={**_updated_payload(), "role": "admin"},
        headers={"Authorization": f"Bearer {_admin_token_with_id(1)}"}
    )

    assert response.status_code == 200
    mock_update.assert_called_once()


def test_update_employee_requires_admin_role():
    response = client.put(
        "/employees/3",
        json=_updated_payload(),
        headers={"Authorization": f"Bearer {_employee_token()}"}
    )

    assert response.status_code == 403


@patch("server.src.routes.employee_routes.payroll_repository.set_employee_active")
def test_deactivate_employee_success(mock_set_active):
    mock_set_active.return_value = {
        "id": 3, "name": "Ana Lopez", "email": "ana@cen.com",
        "role": "employee", "base_salary": 19000, "is_active": False
    }

    response = client.post(
        "/employees/3/deactivate",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert mock_set_active.call_args[0] == (3, False, ADMIN_COMPANY_ID)


@patch("server.src.routes.employee_routes.payroll_repository.set_employee_active")
def test_deactivate_employee_cannot_be_yourself(mock_set_active):
    response = client.post(
        "/employees/1/deactivate",
        headers={"Authorization": f"Bearer {_admin_token_with_id(1)}"}
    )

    assert response.status_code == 400
    mock_set_active.assert_not_called()


@patch("server.src.routes.employee_routes.payroll_repository.set_employee_active")
def test_deactivate_employee_not_found(mock_set_active):
    mock_set_active.return_value = None

    response = client.post(
        "/employees/999/deactivate",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 404


@patch("server.src.routes.employee_routes.payroll_repository.set_employee_active")
def test_activate_employee_success(mock_set_active):
    mock_set_active.return_value = {
        "id": 3, "name": "Ana Lopez", "email": "ana@cen.com",
        "role": "employee", "base_salary": 19000, "is_active": True
    }

    response = client.post(
        "/employees/3/activate",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is True
    assert mock_set_active.call_args[0] == (3, True, ADMIN_COMPANY_ID)


def test_activate_employee_requires_admin_role():
    response = client.post(
        "/employees/3/activate",
        headers={"Authorization": f"Bearer {_employee_token()}"}
    )

    assert response.status_code == 403


@patch("server.src.routes.employee_routes.payroll_repository.set_employee_active")
def test_activate_employee_not_found(mock_set_active):
    mock_set_active.return_value = None

    response = client.post(
        "/employees/999/activate",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 404


@patch("server.src.routes.employee_routes.payroll_repository.reset_password")
def test_reset_password_returns_a_temporary_one(mock_reset):
    mock_reset.return_value = {
        "id": 3, "name": "Ana Lopez", "email": "ana@cen.com",
        "role": "employee", "base_salary": 19000, "is_active": True
    }

    response = client.post(
        "/employees/3/reset-password",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["employee_id"] == 3
    assert len(body["temporary_password"]) >= 8

    employee_id, password_hash, company_id = mock_reset.call_args[0]
    assert company_id == ADMIN_COMPANY_ID
    assert employee_id == 3
    assert password_hash != body["temporary_password"]
    assert password_hash.startswith("$2b$")


@patch("server.src.routes.employee_routes.payroll_repository.reset_password")
def test_reset_password_gives_a_different_one_each_time(mock_reset):
    mock_reset.return_value = {
        "id": 3, "name": "Ana Lopez", "email": "ana@cen.com",
        "role": "employee", "base_salary": 19000, "is_active": True
    }
    headers = {"Authorization": f"Bearer {_admin_token()}"}

    first = client.post("/employees/3/reset-password", headers=headers).json()
    second = client.post("/employees/3/reset-password", headers=headers).json()

    assert first["temporary_password"] != second["temporary_password"]


@patch("server.src.routes.employee_routes.payroll_repository.reset_password")
def test_reset_password_for_a_missing_employee(mock_reset):
    mock_reset.return_value = None

    response = client.post(
        "/employees/999/reset-password",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 404


@patch("server.src.routes.employee_routes.payroll_repository.reset_password")
def test_reset_password_cannot_be_yourself(mock_reset):
    response = client.post(
        "/employees/1/reset-password",
        headers={"Authorization": f"Bearer {_admin_token_with_id(1)}"}
    )

    assert response.status_code == 400
    mock_reset.assert_not_called()


def test_reset_password_requires_admin_role():
    response = client.post(
        "/employees/3/reset-password",
        headers={"Authorization": f"Bearer {_employee_token()}"}
    )

    assert response.status_code == 403


@patch("server.src.routes.employee_routes.payroll_repository.update_employee")
def test_admins_can_have_no_salary(mock_update):
    mock_update.return_value = {
        "id": 4, "name": "Pablo", "email": "pablo@cen.com",
        "role": "admin", "base_salary": None, "is_active": True
    }

    response = client.put(
        "/employees/4",
        json={"name": "Pablo", "email": "pablo@cen.com", "role": "admin",
              "base_salary": None},
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    assert response.json()["base_salary"] is None


def test_employees_need_a_salary():
    response = client.put(
        "/employees/4",
        json={"name": "Ana", "email": "ana@cen.com", "role": "employee",
              "base_salary": None},
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 422


@patch("server.src.routes.employee_routes.payroll_repository.create_employee")
def test_create_an_assimilated_with_its_workday(mock_create_employee):
    mock_create_employee.return_value = 11

    response = client.post(
        "/employees",
        json={
            "name": "Rosa Diaz", "email": "rosa@cen.com", "role": "employee",
            "base_salary": 15000, "password": "clave123",
            "tipo_regimen": "09", "tipo_jornada": "01",
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    assert response.json()["tipo_regimen"] == "09"
    data = mock_create_employee.call_args[0][0]
    assert (data["tipo_regimen"], data["tipo_jornada"]) == ("09", "01")


@patch("server.src.routes.employee_routes.payroll_repository.create_employee")
def test_without_regime_the_person_is_on_salary(mock_create_employee):
    mock_create_employee.return_value = 12

    response = client.post(
        "/employees",
        json={
            "name": "Rosa Diaz", "email": "rosa@cen.com", "role": "employee",
            "base_salary": 15000, "password": "clave123",
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    body = response.json()
    assert (body["tipo_regimen"], body["tipo_jornada"]) == ("02", "01")


@pytest.mark.parametrize("campo, valor", [
    ("tipo_regimen", "05"), ("tipo_jornada", "08"),
])
def test_unsupported_regime_or_workday_is_rejected(campo, valor):
    response = client.post(
        "/employees",
        json={
            "name": "Rosa Diaz", "email": "rosa@cen.com", "role": "employee",
            "base_salary": 15000, "password": "clave123", campo: valor,
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 422


@patch("server.src.routes.employee_routes.payroll_repository.update_employee")
def test_update_changes_the_regime_and_workday(mock_update):
    mock_update.return_value = {
        "id": 3, "name": "Ana", "email": "ana@cen.com", "role": "employee",
        "base_salary": 18000, "is_active": True,
        "tipo_regimen": "02", "tipo_jornada": "03",
    }

    response = client.put(
        "/employees/3",
        json={
            "name": "Ana", "email": "ana@cen.com", "role": "employee",
            "base_salary": 18000, "tipo_regimen": "02", "tipo_jornada": "03",
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    assert response.json()["tipo_jornada"] == "03"
    data = mock_update.call_args[0][1]
    assert (data["tipo_regimen"], data["tipo_jornada"]) == ("02", "03")


def _new_employee(**extra):
    return {
        "name": "Juan Perez", "email": "juan@cen.com", "role": "employee",
        "base_salary": 12000, "password": "clave123", **extra,
    }


@patch("server.src.routes.employee_routes.payroll_repository.create_employee")
def test_create_employee_saves_the_hire_date(mock_create_employee):
    mock_create_employee.return_value = 10

    response = client.post(
        "/employees",
        json=_new_employee(hire_date="2019-06-03"),
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    assert response.json()["hire_date"] == "2019-06-03"
    assert mock_create_employee.call_args[0][0]["hire_date"] == date(2019, 6, 3)


@patch("server.src.routes.employee_routes.payroll_repository.create_employee")
def test_without_hire_date_the_person_starts_today(mock_create_employee):
    mock_create_employee.return_value = 10

    response = client.post(
        "/employees",
        json=_new_employee(),
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.json()["hire_date"] == date.today().isoformat()
    assert mock_create_employee.call_args[0][0]["hire_date"] == date.today()


@patch("server.src.routes.employee_routes.payroll_repository.create_employee")
def test_an_impossible_hire_date_is_rejected(mock_create_employee):
    response = client.post(
        "/employees",
        json=_new_employee(hire_date="2019-02-30"),
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 422
    mock_create_employee.assert_not_called()


@patch("server.src.routes.employee_routes.payroll_repository.update_employee")
def test_update_corrects_the_hire_date(mock_update):
    mock_update.return_value = {
        "id": 3, "name": "Ana", "email": "ana@cen.com", "role": "employee",
        "base_salary": 18000, "is_active": True,
        "tipo_regimen": "02", "tipo_jornada": "01",
        "hire_date": date(2018, 1, 8),
    }

    response = client.put(
        "/employees/3",
        json={
            "name": "Ana", "email": "ana@cen.com", "role": "employee",
            "base_salary": 18000, "hire_date": "2018-01-08",
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    assert response.json()["hire_date"] == "2018-01-08"
    assert mock_update.call_args[0][1]["hire_date"] == date(2018, 1, 8)


@patch("server.src.routes.employee_routes.payroll_repository.update_employee")
def test_update_without_hire_date_keeps_the_saved_one(mock_update):
    mock_update.return_value = {
        "id": 3, "name": "Ana", "email": "ana@cen.com", "role": "employee",
        "base_salary": 18000, "is_active": True,
        "hire_date": date(2018, 1, 8),
    }

    client.put(
        "/employees/3",
        json={
            "name": "Ana", "email": "ana@cen.com", "role": "employee",
            "base_salary": 18000,
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert mock_update.call_args[0][1]["hire_date"] is None


CURP_ANA = "HEGG560427MVZRRL04"
RFC_ANA = "HEGG560427AB1"
NSS_ANA = "92988084494"


@patch("server.src.routes.employee_routes.payroll_repository.create_employee")
def test_create_employee_with_fiscal_ids_normalized(mock_create_employee):
    mock_create_employee.return_value = 10

    response = client.post(
        "/employees",
        json=_new_employee(
            rfc=" hegg560427ab1", curp="hegg560427mvzrrl04",
            nss="92-98-80-8449-4",
        ),
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    data = mock_create_employee.call_args[0][0]
    assert (data["rfc"], data["curp"], data["nss"]) == (RFC_ANA, CURP_ANA, NSS_ANA)
    assert response.json()["curp"] == CURP_ANA


@pytest.mark.parametrize("field, value, message", [
    ("curp", "HEGG560427MVZRRL05", "dígito verificador de la CURP"),
    ("nss", "92988084495", "dígito verificador del NSS"),
    ("rfc", "HEGG5604271", "13 caracteres"),
])
@patch("server.src.routes.employee_routes.payroll_repository.create_employee")
def test_invalid_fiscal_ids_are_rejected_with_the_reason(
    mock_create_employee, field, value, message
):
    response = client.post(
        "/employees",
        json=_new_employee(**{field: value}),
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 422
    assert message in response.json()["detail"][0]["msg"]
    mock_create_employee.assert_not_called()


@patch("server.src.routes.employee_routes.payroll_repository.create_employee")
def test_rfc_and_curp_must_share_the_birth_date(mock_create_employee):
    response = client.post(
        "/employees",
        json=_new_employee(rfc="HEGG560428AB1", curp=CURP_ANA),
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 422
    assert "misma fecha de nacimiento" in response.json()["detail"][0]["msg"]


class _CurpTaken(psycopg2_errors.UniqueViolation):
    @property
    def diag(self):
        return type("Diag", (), {"constraint_name": "employees_curp_key"})()


@patch("server.src.routes.employee_routes.payroll_repository.create_employee")
def test_a_curp_that_another_person_has_is_a_conflict(mock_create_employee):
    mock_create_employee.side_effect = _CurpTaken()

    response = client.post(
        "/employees",
        json=_new_employee(curp=CURP_ANA),
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Esa CURP ya la tiene otra persona"


@patch("server.src.routes.employee_routes.payroll_repository.update_employee")
def test_update_sends_the_fiscal_ids_and_when_the_salary_applies(mock_update):
    mock_update.return_value = {
        "id": 3, "name": "Ana", "email": "ana@cen.com", "role": "employee",
        "base_salary": 21000, "is_active": True, "curp": CURP_ANA,
    }

    response = client.put(
        "/employees/3",
        json={
            "name": "Ana", "email": "ana@cen.com", "role": "employee",
            "base_salary": 21000, "curp": CURP_ANA,
            "salary_valid_from": "2026-10-01",
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    data = mock_update.call_args[0][1]
    assert data["curp"] == CURP_ANA
    assert data["rfc"] is None
    assert data["salary_valid_from"] == date(2026, 10, 1)


@patch("server.src.routes.employee_routes.payroll_repository.salary_history")
def test_salary_history_of_a_person(mock_history):
    mock_history.return_value = [
        {"base_salary": 21000, "valid_from": date(2026, 10, 1),
         "recorded_at": "2026-09-28T10:00:00+00:00", "recorded_by": "Admin"},
        {"base_salary": 19000, "valid_from": date(2020, 1, 15),
         "recorded_at": "2026-09-28T09:00:00+00:00", "recorded_by": None},
    ]

    response = client.get(
        "/employees/3/salary-history",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    assert [row["valid_from"] for row in response.json()] == [
        "2026-10-01", "2020-01-15"
    ]
    assert mock_history.call_args[0] == (3, ADMIN_COMPANY_ID)


@patch("server.src.routes.employee_routes.payroll_repository.salary_history")
def test_salary_history_of_someone_from_another_company(mock_history):
    mock_history.return_value = None

    response = client.get(
        "/employees/3/salary-history",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 404


def test_salary_history_is_only_for_admins():
    response = client.get(
        "/employees/3/salary-history",
        headers={"Authorization": f"Bearer {_employee_token()}"}
    )

    assert response.status_code == 403


EMPLOYEES = "server.src.routes.employee_routes.payroll_repository"
EXISTING = {"id": 3, "role": "employee", "curp": CURP_ANA, "email": "ana@cen.com"}


def _linked_row(**overrides):
    row = {
        "id": 3, "name": "Ana", "email": "ana@cen.com", "role": "employee",
        "base_salary": 15000, "is_active": True, "tipo_regimen": "09",
        "tipo_jornada": "01", "hire_date": date(2024, 6, 1), "rfc": None,
        "curp": CURP_ANA, "nss": None,
    }
    row.update(overrides)
    return row


@patch(EMPLOYEES + ".create_employee")
@patch(EMPLOYEES + ".hire_existing_employee")
def test_an_existing_person_is_linked_with_the_same_curp(
    mock_hire, mock_create, email_lookup
):
    email_lookup.return_value = dict(EXISTING)
    mock_hire.return_value = _linked_row()

    response = client.post(
        "/employees",
        json=_new_employee(
            email="ANA@cen.com", curp=CURP_ANA, base_salary=15000,
            tipo_regimen="09", hire_date="2024-06-01",
        ),
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    assert response.json()["linked"] is True
    mock_create.assert_not_called()
    employee_id, data, company_id, actor_id = mock_hire.call_args[0]
    assert (employee_id, company_id, actor_id) == (3, ADMIN_COMPANY_ID, 99)
    assert data == {
        "base_salary": 15000, "tipo_regimen": "09", "tipo_jornada": "01",
        "hire_date": date(2024, 6, 1),
    }


@pytest.mark.parametrize("curp", [None, "SABC560626MDFLRN01"])
@patch(EMPLOYEES + ".hire_existing_employee")
def test_linking_needs_the_curp_the_person_has(mock_hire, email_lookup, curp):
    email_lookup.return_value = dict(EXISTING)
    extra = {"curp": curp} if curp else {}

    response = client.post(
        "/employees", json=_new_employee(email="ana@cen.com", **extra),
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 409
    assert "captura su CURP" in response.json()["detail"]
    mock_hire.assert_not_called()


@pytest.mark.parametrize("existing_role, requested_role", [
    ("admin", "employee"), ("owner", "employee"), ("employee", "admin"),
])
@patch(EMPLOYEES + ".hire_existing_employee")
def test_only_employees_are_linked(
    mock_hire, email_lookup, existing_role, requested_role
):
    email_lookup.return_value = {**EXISTING, "role": existing_role}

    response = client.post(
        "/employees",
        json=_new_employee(email="ana@cen.com", curp=CURP_ANA, role=requested_role),
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "El correo ya está registrado"
    mock_hire.assert_not_called()


@pytest.mark.parametrize("is_active, detail", [
    (True, "Esa persona ya está en tu empresa"),
    (False, "Esa persona ya estuvo en tu empresa: reactívala desde Usuarios"),
])
@patch(EMPLOYEES + ".hire_existing_employee")
def test_linking_someone_already_here(mock_hire, email_lookup, is_active, detail):
    from server.src.repositories.payroll_repository import AlreadyEmployedError

    email_lookup.return_value = dict(EXISTING)
    mock_hire.side_effect = AlreadyEmployedError(is_active)

    response = client.post(
        "/employees", json=_new_employee(email="ana@cen.com", curp=CURP_ANA),
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 409
    assert response.json()["detail"] == detail


@patch(EMPLOYEES + ".update_employee")
def test_the_identity_of_someone_who_works_elsewhere_stays(mock_update):
    from server.src.repositories.payroll_repository import SharedPersonError

    mock_update.side_effect = SharedPersonError()

    response = client.put(
        "/employees/3",
        json={
            "name": "Otra", "email": "ana@cen.com", "role": "employee",
            "base_salary": 18000,
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 409
    assert "no su nombre" in response.json()["detail"]


@patch(EMPLOYEES + ".reset_password")
def test_the_password_of_someone_who_works_elsewhere(mock_reset):
    from server.src.repositories.payroll_repository import SharedPersonError

    mock_reset.side_effect = SharedPersonError()

    response = client.post(
        "/employees/3/reset-password",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 409
    assert "recuperar su contraseña" in response.json()["detail"]
