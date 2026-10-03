import random
import string

import pytest
from fastapi.testclient import TestClient

from server.src.main import app
from server.src.middlewares.auth_middleware import (
    create_access_token,
    hash_password,
)
from server.src.models.fiscal_ids import curp_check_digit
from server.src.repositories.auth_repository import AuthRepository
from server.src.repositories.company_repository import company_repository
from server.src.repositories.payroll_repository import payroll_repository
from server.tests.integration.conftest import company_with_admin, unique_email

client = TestClient(app)
sessions = AuthRepository()

PASSWORD_HASH = hash_password("clave-de-prueba")
CONSONANTS = "BCDFGHJKLMNPQRSTVWXYZ"


def _new_curp() -> str:
    first = (
        random.choice(CONSONANTS) + random.choice("AEIOU")
        + "".join(random.choice(string.ascii_uppercase) for _ in range(2))
        + "{:02d}{:02d}{:02d}".format(
            random.randint(40, 99), random.randint(1, 12), random.randint(1, 28)
        )
        + random.choice("HM") + "SL"
        + "".join(random.choice(CONSONANTS) for _ in range(3)) + "0"
    )
    return first + str(curp_check_digit(first))


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
    return (
        company_with_admin(superadmin, owner, PASSWORD_HASH),
        company_with_admin(superadmin, owner, PASSWORD_HASH),
    )


def _hire(company: dict, email: str, **extra):
    return client.post("/employees", json={
        "name": "Ana Ruiz", "email": email, "role": "employee",
        "base_salary": 19000, "password": "clave1234",
        "hire_date": "2020-01-15", **extra,
    }, headers=company["headers"])


@pytest.fixture
def person(companies):
    first, _ = companies
    email, curp = unique_email("ana"), _new_curp()
    response = _hire(first, email, curp=curp)
    assert response.status_code == 200, response.text
    return {"id": response.json()["id"], "email": email, "curp": curp}


@pytest.fixture
def shared(companies, person):
    _, second = companies
    response = _hire(
        second, person["email"].upper(), curp=person["curp"],
        base_salary=15000, tipo_regimen="09", hire_date="2024-06-01",
    )
    assert response.status_code == 200, response.text
    return {**person, "link": response.json()}


def _employee_headers(employee_id: int) -> dict:
    payroll_repository.update_password(employee_id, PASSWORD_HASH)
    version = sessions.session_state(employee_id, "employee")["token_version"]
    token = create_access_token(data={
        "sub": "ana@pruebas.cen", "role": "employee",
        "employee_id": employee_id, "ver": version,
    })
    return {"Authorization": "Bearer " + token}


def test_the_email_and_the_curp_link_the_same_person(companies, shared):
    first, second = companies

    assert shared["link"]["id"] == shared["id"]
    assert shared["link"]["linked"] is True
    here = payroll_repository.get_employee_by_id(shared["id"], second["id"])
    there = payroll_repository.get_employee_by_id(shared["id"], first["id"])
    assert (here["base_salary"], here["tipo_regimen"], str(here["hire_date"])) == (
        15000, "09", "2024-06-01"
    )
    assert (there["base_salary"], there["tipo_regimen"]) == (19000, "02")


def test_linking_needs_the_curp_the_person_already_has(companies, person):
    _, second = companies

    without = _hire(second, person["email"])
    wrong = _hire(second, person["email"], curp=_new_curp())

    assert without.status_code == wrong.status_code == 409
    assert "captura su CURP" in without.json()["detail"]
    assert payroll_repository.get_employee_by_id(person["id"], second["id"]) is None


def test_linking_twice_is_a_conflict(companies, shared):
    _, second = companies

    response = _hire(second, shared["email"], curp=shared["curp"])

    assert response.status_code == 409
    assert response.json()["detail"] == "Esa persona ya está en tu empresa"


def test_both_companies_pay_the_same_period(companies, shared):
    first, second = companies
    for company, salary in ((first, 19000), (second, 15000)):
        response = client.post("/payroll/calculate", json={
            "employee_id": shared["id"], "period_start": "2026-09-01",
            "gross_salary": salary,
        }, headers=company["headers"])
        assert response.status_code == 200, response.text

    receipts = client.get(
        "/payroll/my-receipts", headers=_employee_headers(shared["id"])
    ).json()

    assert receipts["total"] == 2
    assert {item["company_name"] for item in receipts["items"]} == {
        row["legal_name"]
        for row in company_repository.list_companies()
        if row["id"] in (first["id"], second["id"])
    }
    assert {item["tipo_regimen"] for item in receipts["items"]} == {"02", "09"}


def test_the_second_company_changes_the_job_not_the_person(companies, shared):
    _, second = companies
    base = {
        "name": "Ana Ruiz", "email": shared["email"], "role": "employee",
        "base_salary": 16000, "tipo_regimen": "09",
    }

    renamed = client.put(
        f"/employees/{shared['id']}", json={**base, "name": "Otra Persona"},
        headers=second["headers"],
    )
    raised = client.put(
        f"/employees/{shared['id']}", json=base, headers=second["headers"],
    )

    assert renamed.status_code == 409
    assert "no su nombre" in renamed.json()["detail"]
    assert raised.status_code == 200, raised.text
    assert raised.json()["base_salary"] == 16000


def test_the_second_company_cannot_reset_the_password(companies, shared):
    _, second = companies

    response = client.post(
        f"/employees/{shared['id']}/reset-password", headers=second["headers"]
    )

    assert response.status_code == 409
    assert "recuperar su contraseña" in response.json()["detail"]


def test_leaving_one_company_keeps_the_account(companies, shared):
    first, second = companies

    response = client.post(
        f"/employees/{shared['id']}/deactivate", headers=second["headers"]
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert payroll_repository.get_employee_by_id(
        shared["id"], first["id"]
    )["is_active"] is True
    state = sessions.session_state(shared["id"], "employee")
    assert state["is_active"] is True
    assert state["company_is_active"] is True


def test_leaving_the_only_company_closes_the_account(companies, person):
    first, _ = companies

    client.post(f"/employees/{person['id']}/deactivate", headers=first["headers"])
    closed = sessions.session_state(person["id"], "employee")
    client.post(f"/employees/{person['id']}/activate", headers=first["headers"])
    reopened = sessions.session_state(person["id"], "employee")

    assert closed["is_active"] is False
    assert reopened["is_active"] is True


def test_an_admin_cannot_be_linked_as_an_employee(companies):
    first, second = companies
    admin_email = next(
        row["email"] for row in payroll_repository.list_employees(first["id"])
        if row["id"] == first["admin"]
    )

    response = _hire(second, admin_email, curp=_new_curp())

    assert response.status_code == 409
    assert response.json()["detail"] == "El correo ya está registrado"
