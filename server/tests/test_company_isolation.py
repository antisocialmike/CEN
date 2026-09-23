"""Aislamiento entre empresas.

El admin de la empresa A (id 1) no puede leer ni escribir nada de la B (id 2),
un admin de A y B trabaja en la que indique la cabecera, y los duenos solo
cuentan como tales en sus propias empresas.
"""
from datetime import date
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from server.src.main import app
from server.src.middlewares.auth_middleware import create_access_token
from server.src.middlewares.company_context import (
    COMPANY_HEADER,
    ensure_owner_company,
    resolve_admin_company,
)
from server.src.repositories.payroll_repository import (
    ReceiptOfAnotherCompanyError,
    SharedAdminError,
)

client = TestClient(app)

COMPANY_A = 1
COMPANY_B = 2
CONTEXT = "server.src.middlewares.company_context.company_repository"
PAYROLL = "server.src.routes.payroll_routes.payroll_repository"
EMPLOYEES = "server.src.routes.employee_routes.payroll_repository"


def _token(role: str, employee_id: int = 10, **extra) -> str:
    return create_access_token(data={
        "sub": role + "@cen.com", "role": role,
        "employee_id": employee_id, **extra,
    })


def _headers(role: str = "admin", company=None, **extra) -> dict:
    headers = {"Authorization": f"Bearer {_token(role, **extra)}"}
    if company is not None:
        headers[COMPANY_HEADER] = str(company)
    return headers


@pytest.fixture
def admin_of():
    """Parchea las empresas que administra el admin del token."""
    def configure(*companies):
        repository.admin_company_ids.return_value = list(companies)
        repository.admin_has_company.side_effect = (
            lambda admin_id, company_id: company_id in companies
        )
        return repository

    with patch(CONTEXT) as repository:
        yield configure


# --- Resolver la empresa activa ---------------------------------------------

def test_an_admin_of_a_single_company_needs_no_header(admin_of):
    admin_of(COMPANY_A)

    assert resolve_admin_company({"employee_id": 10}, None) == COMPANY_A


def test_an_admin_of_several_companies_must_choose(admin_of):
    admin_of(COMPANY_A, COMPANY_B)

    with pytest.raises(HTTPException) as error:
        resolve_admin_company({"employee_id": 10}, None)

    assert error.value.status_code == 400


def test_an_admin_without_companies_is_turned_away(admin_of):
    admin_of()

    with pytest.raises(HTTPException) as error:
        resolve_admin_company({"employee_id": 10}, None)

    assert error.value.status_code == 403


def test_a_foreign_company_looks_like_it_does_not_exist(admin_of):
    admin_of(COMPANY_A)

    with pytest.raises(HTTPException) as error:
        resolve_admin_company({"employee_id": 10}, COMPANY_B)

    assert error.value.status_code == 404


def test_owners_only_reach_their_own_companies():
    with patch(CONTEXT) as repository:
        repository.owner_has_company.side_effect = (
            lambda owner_id, company_id: company_id == COMPANY_A
        )

        assert ensure_owner_company({"employee_id": 20}, COMPANY_A) == COMPANY_A
        with pytest.raises(HTTPException) as error:
            ensure_owner_company({"employee_id": 20}, COMPANY_B)

    assert error.value.status_code == 404


# --- El admin de A contra la empresa B ---------------------------------------

@pytest.mark.parametrize("method, path, body", [
    ("get", "/employees", None),
    ("post", "/employees", {
        "name": "X", "email": "x@b.mx", "role": "employee",
        "base_salary": 1, "password": "clave1234",
    }),
    ("put", "/employees/5", {
        "name": "X", "email": "x@b.mx", "role": "employee", "base_salary": 1,
    }),
    ("post", "/employees/5/deactivate", None),
    ("post", "/employees/5/reset-password", None),
    ("get", "/payroll/receipts", None),
    ("post", "/payroll/lookup", {
        "employee_id": 5, "periodicity": "mensual",
        "period_start": "2026-09-01",
    }),
    ("post", "/payroll/calculate", {
        "employee_id": 5, "period_start": "2026-09-01", "gross_salary": 1000,
    }),
])
def test_an_admin_of_a_cannot_touch_company_b(admin_of, method, path, body):
    admin_of(COMPANY_A)

    with patch(EMPLOYEES) as employees, patch(PAYROLL) as payroll:
        response = client.request(
            method, path, json=body, headers=_headers(company=COMPANY_B)
        )

    assert response.status_code == 404
    assert employees.method_calls == []
    assert payroll.method_calls == []


@patch(EMPLOYEES + ".list_employees")
def test_an_admin_of_a_and_b_works_in_the_chosen_one(mock_list, admin_of):
    admin_of(COMPANY_A, COMPANY_B)
    mock_list.return_value = []

    response = client.get("/employees", headers=_headers(company=COMPANY_B))

    assert response.status_code == 200
    mock_list.assert_called_once_with(COMPANY_B)


def test_an_admin_of_a_and_b_without_header_is_asked_to_choose(admin_of):
    admin_of(COMPANY_A, COMPANY_B)

    response = client.get("/employees", headers=_headers())

    assert response.status_code == 400
    assert COMPANY_HEADER in response.json()["detail"]


@patch(EMPLOYEES + ".create_employee")
def test_new_people_join_the_active_company(mock_create, admin_of):
    admin_of(COMPANY_A, COMPANY_B)
    mock_create.return_value = 30

    client.post("/employees", json={
        "name": "Nuevo", "email": "nuevo@b.mx", "role": "employee",
        "base_salary": 1000, "password": "clave1234",
    }, headers=_headers(company=COMPANY_B, employee_id=10))

    _, company_id, actor_id = mock_create.call_args[0]
    assert (company_id, actor_id) == (COMPANY_B, 10)


@patch(EMPLOYEES + ".update_employee")
def test_an_employee_of_b_is_not_found_from_a(mock_update, admin_of):
    admin_of(COMPANY_A)
    mock_update.return_value = None

    response = client.put("/employees/5", json={
        "name": "X", "email": "x@b.mx", "role": "employee", "base_salary": 1,
    }, headers=_headers())

    assert response.status_code == 404
    assert mock_update.call_args[0][2] == COMPANY_A


@pytest.mark.parametrize("method, path, body", [
    ("put", "/employees/5", {
        "name": "X", "email": "x@b.mx", "role": "admin", "base_salary": 1,
    }),
    ("post", "/employees/5/deactivate", None),
    ("post", "/employees/5/activate", None),
    ("post", "/employees/5/reset-password", None),
])
def test_an_admin_shared_with_other_companies_is_left_alone(
    admin_of, method, path, body
):
    admin_of(COMPANY_A)

    with patch(EMPLOYEES) as employees:
        employees.update_employee.side_effect = SharedAdminError()
        employees.set_employee_active.side_effect = SharedAdminError()
        employees.reset_password.side_effect = SharedAdminError()
        response = client.request(method, path, json=body, headers=_headers())

    assert response.status_code == 409
    assert "otras empresas" in response.json()["detail"]


# --- Nomina ------------------------------------------------------------------

@patch(PAYROLL + ".save_payroll_receipt")
@patch(PAYROLL + ".get_employee_by_id")
def test_payroll_is_issued_by_the_active_company(
    mock_get, mock_save, admin_of
):
    admin_of(COMPANY_A, COMPANY_B)
    mock_get.return_value = {"id": 5, "name": "Ana", "is_active": True}
    mock_save.return_value = {"id": 9, "created": True}

    response = client.post("/payroll/calculate", json={
        "employee_id": 5, "period_start": "2026-09-01", "gross_salary": 20000,
    }, headers=_headers(company=COMPANY_B))

    assert response.status_code == 200
    mock_get.assert_called_once_with(5, COMPANY_B)
    assert mock_save.call_args[0][0]["company_id"] == COMPANY_B


@patch(PAYROLL + ".get_employee_by_id")
def test_payroll_for_somebody_outside_the_company(mock_get, admin_of):
    admin_of(COMPANY_A)
    mock_get.return_value = None

    response = client.post("/payroll/calculate", json={
        "employee_id": 5, "period_start": "2026-09-01", "gross_salary": 20000,
    }, headers=_headers())

    assert response.status_code == 404


@patch(PAYROLL + ".save_payroll_receipt")
@patch(PAYROLL + ".get_employee_by_id")
def test_a_period_already_paid_by_another_company(
    mock_get, mock_save, admin_of
):
    admin_of(COMPANY_A)
    mock_get.return_value = {"id": 5, "name": "Ana", "is_active": True}
    mock_save.side_effect = ReceiptOfAnotherCompanyError()

    response = client.post("/payroll/calculate", json={
        "employee_id": 5, "period_start": "2026-09-01", "gross_salary": 20000,
    }, headers=_headers())

    assert response.status_code == 409


def _receipt(company_id: int, employee_id: int = 5) -> dict:
    return {
        "id": 42, "employee_id": employee_id, "company_id": company_id,
        "employee_name": "Ana", "employee_email": "ana@cen.com",
        "period_start": date(2026, 9, 1), "period_end": date(2026, 9, 30),
        "periodicity": "mensual", "paid_days": 30, "gross_salary": 21000,
        "isr_deduction": 2612.86, "imss_deduction": 583.0,
        "net_salary": 17804.14, "processed_by": "admin@cen.com",
        "created_at": date(2026, 9, 8),
    }


@patch(PAYROLL + ".get_receipt_by_id")
def test_an_admin_of_a_cannot_download_a_receipt_of_b(mock_get, admin_of):
    admin_of(COMPANY_A)
    mock_get.return_value = _receipt(COMPANY_B)

    response = client.get("/payroll/receipts/42/pdf", headers=_headers())

    assert response.status_code == 404


@patch(PAYROLL + ".get_receipt_by_id")
def test_an_admin_downloads_receipts_of_the_active_company(
    mock_get, admin_of
):
    admin_of(COMPANY_A, COMPANY_B)
    mock_get.return_value = _receipt(COMPANY_B)

    response = client.get(
        "/payroll/receipts/42/pdf", headers=_headers(company=COMPANY_B)
    )

    assert response.status_code == 200


@patch(PAYROLL + ".get_receipt_by_id")
def test_an_admin_keeps_access_to_their_own_receipts(mock_get, admin_of):
    admin_of(COMPANY_A)
    mock_get.return_value = _receipt(COMPANY_B, employee_id=10)

    response = client.get(
        "/payroll/receipts/42/pdf", headers=_headers(employee_id=10)
    )

    assert response.status_code == 200


# --- Empleados, duenos y superadmin ------------------------------------------

@patch("server.src.routes.auth_routes.payroll_repository")
def test_the_employee_token_carries_its_company(repository):
    from jose import jwt

    from server.src.config.settings import JWT_ALGORITHM, JWT_SECRET_KEY
    from server.src.middlewares.auth_middleware import hash_password

    repository.get_employee_by_email.return_value = {
        "id": 5, "email": "ana@cen.com", "role": "employee", "name": "Ana",
        "company_id": COMPANY_B, "password_hash": hash_password("clave123"),
    }

    response = client.post(
        "/auth/login", json={"email": "ana@cen.com", "password": "clave123"}
    )

    claims = jwt.decode(
        response.json()["access_token"], JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
    )
    assert claims["company_id"] == COMPANY_B


@pytest.mark.parametrize("role", ["owner", "superadmin", "employee"])
@pytest.mark.parametrize("path", ["/employees", "/payroll/receipts"])
def test_only_admins_operate_payroll(role, path):
    response = client.get(path, headers=_headers(role, company=COMPANY_A))

    assert response.status_code == 403
