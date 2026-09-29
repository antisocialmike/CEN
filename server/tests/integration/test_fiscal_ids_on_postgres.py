import uuid
from datetime import date
from decimal import Decimal

import psycopg2
import pytest
from fastapi.testclient import TestClient

from server.src.main import app
from server.src.middlewares.auth_middleware import (
    create_access_token,
    hash_password,
)
from server.src.repositories.company_repository import company_repository
from server.src.repositories.payroll_repository import payroll_repository
from server.tests.integration.conftest import database_before, unique_email

client = TestClient(app)

PASSWORD_HASH = hash_password("clave-de-prueba")
CURP_ANA = "HEGG560427MVZRRL04"
RFC_ANA = "HEGG560427AB1"
NSS_ANA = "92988084494"


def _company(superadmin: int, owner: int) -> dict:
    company = company_repository.create_company(
        {"legal_name": "Empresa " + uuid.uuid4().hex[:6]}, owner, superadmin
    )
    admin = company_repository.invite_admin(company, {
        "name": "Admin", "email": unique_email("admin"),
        "password_hash": PASSWORD_HASH,
    }, owner)
    payroll_repository.update_password(admin, PASSWORD_HASH)
    token = create_access_token(data={
        "sub": "admin@pruebas.cen", "role": "admin", "employee_id": admin,
        "ver": 1,
    })
    return {
        "id": company,
        "headers": {
            "Authorization": "Bearer " + token, "X-Company-Id": str(company),
        },
    }


@pytest.fixture(scope="module")
def companies():
    superadmin = payroll_repository.create_employee({
        "name": "Super", "email": unique_email("super"), "role": "superadmin",
        "base_salary": None, "password_hash": PASSWORD_HASH,
    })
    owner = company_repository.create_owner({
        "name": "Laura", "email": unique_email("duena"),
        "password_hash": PASSWORD_HASH,
    }, superadmin)
    return _company(superadmin, owner), _company(superadmin, owner)


def _hire(company: dict, **extra):
    return client.post("/employees", json={
        "name": "Ana", "email": unique_email("ana"), "role": "employee",
        "base_salary": 19000, "password": "clave1234",
        "hire_date": "2020-01-15", **extra,
    }, headers=company["headers"])


def test_fiscal_ids_are_saved_normalized(companies):
    first, _ = companies

    response = _hire(
        first, rfc="hegg560427ab1", curp=CURP_ANA, nss="92-98-80-8449-4"
    )

    assert response.status_code == 200, response.text
    saved = payroll_repository.get_employee_by_id(
        response.json()["id"], first["id"]
    )
    assert (saved["rfc"], saved["curp"], saved["nss"]) == (
        RFC_ANA, CURP_ANA, NSS_ANA
    )


def test_the_same_curp_twice_in_a_company_is_a_conflict(companies):
    first, _ = companies
    curp = "SABC560626MDFLRN01"
    assert _hire(first, curp=curp).status_code == 200

    response = _hire(first, curp=curp)

    assert response.status_code == 409
    assert "CURP" in response.json()["detail"]


def test_the_same_person_can_work_in_another_company(companies):
    first, second = companies
    nss = "12345678903"
    assert _hire(first, nss=nss).status_code == 200

    assert _hire(second, nss=nss).status_code == 200


def test_the_database_rejects_a_malformed_curp():
    with pytest.raises(psycopg2.errors.CheckViolation):
        payroll_repository.create_employee({
            "name": "Ana", "email": unique_email("mal"), "role": "employee",
            "base_salary": 1, "password_hash": PASSWORD_HASH, "curp": "MAL",
        }, payroll_repository.first_company_id())


def test_the_salary_history_follows_each_change(companies):
    first, _ = companies
    employee = _hire(first).json()["id"]

    raise_response = client.put(f"/employees/{employee}", json={
        "name": "Ana", "email": unique_email("ana"), "role": "employee",
        "base_salary": 21000, "salary_valid_from": "2026-10-01",
    }, headers=first["headers"])
    same_response = client.put(f"/employees/{employee}", json={
        "name": "Ana Maria", "email": unique_email("ana"), "role": "employee",
        "base_salary": 21000,
    }, headers=first["headers"])
    history = client.get(
        f"/employees/{employee}/salary-history", headers=first["headers"]
    )

    assert raise_response.status_code == 200, raise_response.text
    assert same_response.status_code == 200
    assert [
        (row["base_salary"], row["valid_from"]) for row in history.json()
    ] == [(21000.0, "2026-10-01"), (19000.0, "2020-01-15")]
    assert history.json()[0]["recorded_by"] == "Admin"


def test_the_history_of_another_company_is_not_visible(companies):
    first, second = companies
    employee = _hire(first).json()["id"]

    response = client.get(
        f"/employees/{employee}/salary-history", headers=second["headers"]
    )

    assert response.status_code == 404


def test_the_migration_starts_the_history_with_the_current_salaries():
    with database_before("017") as (connection, migration):
        with connection, connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO employees (name, email, role, base_salary, "
                "password_hash, company_id, hire_date) VALUES "
                "('Ana', 'ana@relleno.cen', 'employee', 19000, 'x', 1, "
                "'2020-01-15'), "
                "('Luis', 'luis@relleno.cen', 'admin', 25000, 'x', NULL, "
                "'2019-03-01'), "
                "('Pablo', 'pablo@relleno.cen', 'admin', NULL, 'x', NULL, "
                "'2021-05-10') RETURNING id;"
            )
            ana, luis, pablo = [row["id"] for row in cursor.fetchall()]
            cursor.execute(
                "INSERT INTO company_admins (admin_id, company_id) "
                "VALUES (%s, 1), (%s, 1);", (luis, pablo),
            )
            cursor.execute(migration)
            cursor.execute(
                "SELECT employee_id, company_id, base_salary, valid_from "
                "FROM salary_history ORDER BY employee_id;"
            )
            rows = [dict(row) for row in cursor.fetchall()]

    assert rows == [
        {"employee_id": ana, "company_id": 1,
         "base_salary": Decimal("19000.00"), "valid_from": date(2020, 1, 15)},
        {"employee_id": luis, "company_id": 1,
         "base_salary": Decimal("25000.00"), "valid_from": date(2019, 3, 1)},
    ]
