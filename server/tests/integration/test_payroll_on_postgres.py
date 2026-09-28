from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from server.src.main import app
from server.src.middlewares.auth_middleware import (
    create_access_token,
    hash_password,
)
from server.src.repositories.company_repository import company_repository
from server.src.repositories.payroll_repository import payroll_repository
from server.tests.integration.conftest import unique_email

client = TestClient(app)

PASSWORD_HASH = hash_password("clave-de-prueba")


def _headers(role: str, employee_id: int, company_id=None) -> dict:
    token = create_access_token(data={
        "sub": role + "@pruebas.cen", "role": role, "employee_id": employee_id,
        "ver": 1,
    })
    headers = {"Authorization": "Bearer " + token}
    if company_id is not None:
        headers["X-Company-Id"] = str(company_id)
    return headers


def _person(name: str, role: str, **extra) -> dict:
    return {
        "name": name, "email": unique_email(name.lower()), "role": role,
        "base_salary": None, "password_hash": PASSWORD_HASH, **extra,
    }


@pytest.fixture(scope="module")
def world():
    superadmin = payroll_repository.create_employee(
        _person("Super", "superadmin")
    )
    owner = company_repository.create_owner(_person("Laura", "owner"), superadmin)
    company = company_repository.create_company(
        {"legal_name": "Grupo Potosino SA de CV", "entidad_federativa": "SLP"},
        owner, superadmin,
    )
    company_repository.set_risk_premium(
        company, Decimal("0.0054355"), date(2026, 1, 1), owner
    )
    admin = company_repository.invite_admin(
        company, _person("Admin", "admin"), owner
    )
    employee = payroll_repository.create_employee(_person(
        "Ana", "employee", base_salary=21000, hire_date=date(2020, 1, 15),
    ), company)
    accounts = {
        "superadmin": superadmin, "owner": owner, "admin": admin,
        "employee": employee,
    }
    for account in accounts.values():
        payroll_repository.update_password(account, PASSWORD_HASH)
    return {**accounts, "company": company}


def _calculate(world, **payload):
    return client.post("/payroll/calculate", json={
        "employee_id": world["employee"], "period_start": "2026-09-01",
        "gross_salary": 21000, **payload,
    }, headers=_headers("admin", world["admin"], world["company"]))


@pytest.fixture(scope="module")
def calculation(world):
    response = _calculate(world)
    assert response.status_code == 200, response.text
    return response.json()


def test_the_hire_date_is_saved_and_read_back(world):
    employee = payroll_repository.get_employee_by_id(
        world["employee"], world["company"]
    )

    assert employee["hire_date"] == date(2020, 1, 15)


def test_the_seniority_of_the_calculation_comes_from_the_hire_date(calculation):
    assert calculation["created"] is True
    assert calculation["employer_cost"]["sbc_daily"] == 739.31


def test_the_receipt_keeps_the_breakdown_to_the_cent(calculation):
    receipt = payroll_repository.get_receipt_by_id(calculation["receipt_id"])

    assert receipt["net_salary"] == Decimal(str(calculation["data"]["net_salary"]))
    assert receipt["isr_deduction"] == Decimal(
        str(calculation["data"]["isr_deduction"])
    )
    assert len(receipt["items"]) == len(calculation["data"]["items"])


def test_recalculating_the_period_replaces_the_receipt(world, calculation):
    response = _calculate(world)

    assert response.status_code == 200
    assert response.json()["created"] is False
    assert response.json()["receipt_id"] == calculation["receipt_id"]


def test_a_period_that_overlaps_is_rejected(world, calculation):
    response = _calculate(world, periodicity="semanal", period_start="2026-09-08")

    assert response.status_code == 409


def test_the_admin_sees_the_receipt_and_the_summary(world, calculation):
    headers = _headers("admin", world["admin"], world["company"])

    receipts = client.get("/payroll/receipts", headers=headers)
    summary = client.get("/admin/summary", headers=headers)

    assert receipts.status_code == 200
    assert [r["id"] for r in receipts.json()["items"]] == [
        calculation["receipt_id"]
    ]
    assert summary.status_code == 200, summary.text


def test_the_employee_sees_the_summary_the_receipts_and_the_pdf(
    world, calculation
):
    headers = _headers("employee", world["employee"])

    summary = client.get("/payroll/my-summary", headers=headers)
    receipts = client.get("/payroll/my-receipts", headers=headers)
    pdf = client.get(
        "/payroll/receipts/{}/pdf".format(calculation["receipt_id"]),
        headers=headers,
    )

    assert summary.status_code == 200, summary.text
    assert summary.json()["latest"]["id"] == calculation["receipt_id"]
    assert receipts.json()["total"] == 1
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"


def test_the_owner_compares_the_company(world, calculation):
    response = client.get(
        "/owner/analytics",
        params={"from": "2026-09-01", "to": "2026-09-30"},
        headers=_headers("owner", world["owner"]),
    )

    assert response.status_code == 200, response.text
    [company] = response.json()["companies"]
    assert company["id"] == world["company"]
    assert company["receipts"] == 1


def test_the_platform_summary_answers(world, calculation):
    response = client.get(
        "/superadmin/summary", headers=_headers("superadmin", world["superadmin"])
    )

    assert response.status_code == 200, response.text


def test_updating_without_hire_date_keeps_the_saved_one(world):
    employee = payroll_repository.create_employee(_person(
        "Beto", "employee", base_salary=15000, hire_date=date(2018, 5, 2),
    ), world["company"])

    updated = payroll_repository.update_employee(employee, {
        "name": "Beto", "email": unique_email("beto"), "role": "employee",
        "base_salary": 16000,
    }, world["company"])

    assert updated["hire_date"] == date(2018, 5, 2)
