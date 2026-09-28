from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from server.src.config.settings import (
    PASSWORD_RESET_COOLDOWN_SECONDS,
    PASSWORD_RESET_MAX_ATTEMPTS,
    PASSWORD_RESET_MAX_PER_HOUR,
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
)
from server.src.main import app
from server.src.middlewares.auth_middleware import (
    hash_reset_code,
    verify_password,
)

client = TestClient(app)

ROUTES = "server.src.routes.auth_routes"
ANA = {
    "id": 7, "email": "ana@cen.com", "name": "Ana", "role": "employee",
    "is_active": True, "company_id": 1, "company_is_active": True,
}


@pytest.fixture
def employee():
    with patch(ROUTES + ".payroll_repository.get_employee_by_email") as lookup:
        lookup.return_value = dict(ANA)
        yield lookup


@pytest.fixture
def codes():
    with patch(ROUTES + ".auth_repository") as repository:
        repository.issue_reset_code.return_value = True
        repository.claim_reset_attempt.return_value = {
            "id": 30, "code_hash": hash_reset_code("123456"),
        }
        repository.reset_password_with_code.return_value = True
        yield repository


@pytest.fixture
def mailer():
    with patch(ROUTES + ".send_password_reset_email") as send:
        yield send


def _request(email="ana@cen.com"):
    return client.post("/auth/password-reset/request", json={"email": email})


def _verify(code="123456", email="ana@cen.com", password="nuevaClave1"):
    return client.post("/auth/password-reset/verify", json={
        "email": email, "code": code, "new_password": password,
    })


def test_request_issues_a_code_and_mails_it(employee, codes, mailer):
    response = _request()

    assert response.status_code == 204
    employee_id, code_hash, minutes, cooldown, hourly = (
        codes.issue_reset_code.call_args[0]
    )
    assert employee_id == 7
    assert (minutes, cooldown, hourly) == (
        PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
        PASSWORD_RESET_COOLDOWN_SECONDS,
        PASSWORD_RESET_MAX_PER_HOUR,
    )
    # A la base va el HMAC; el codigo en claro solo viaja en el correo.
    mailed_code = mailer.call_args.kwargs["code"]
    assert code_hash == hash_reset_code(mailed_code)
    assert code_hash != mailed_code
    assert mailer.call_args.kwargs["email"] == "ana@cen.com"


def test_request_for_an_unknown_email_answers_the_same(employee, codes, mailer):
    employee.return_value = None

    response = _request("nadie@cen.com")

    assert response.status_code == 204
    codes.issue_reset_code.assert_not_called()
    mailer.assert_not_called()


@pytest.mark.parametrize("state", [
    {"is_active": False},
    {"company_is_active": False},
])
def test_request_ignores_accounts_that_cannot_enter(
    state, employee, codes, mailer
):
    employee.return_value = {**ANA, **state}

    response = _request()

    assert response.status_code == 204
    codes.issue_reset_code.assert_not_called()
    mailer.assert_not_called()


def test_request_inside_the_cooldown_sends_nothing(employee, codes, mailer):
    codes.issue_reset_code.return_value = False

    response = _request()

    assert response.status_code == 204
    mailer.assert_not_called()


def test_request_is_limited_by_address(employee, codes, rate_limit_window):
    rate_limit_window.return_value = {"hits": 6, "retry_after": 600}

    response = _request()

    assert response.status_code == 429
    employee.assert_not_called()
    assert rate_limit_window.call_args[0][0] == "password-reset-request"


def test_verify_with_the_right_code_sets_the_password(employee, codes):
    response = _verify()

    assert response.status_code == 204
    codes.claim_reset_attempt.assert_called_once_with(
        7, PASSWORD_RESET_MAX_ATTEMPTS
    )
    code_id, employee_id, password_hash = (
        codes.reset_password_with_code.call_args[0]
    )
    assert (code_id, employee_id) == (30, 7)
    assert verify_password("nuevaClave1", password_hash)


def test_verify_looks_for_the_code_only_in_that_account(employee, codes):
    _verify(email="ana@cen.com")

    employee.assert_called_once_with("ana@cen.com")
    assert codes.claim_reset_attempt.call_args[0][0] == ANA["id"]


def test_verify_with_a_wrong_code_spends_the_attempt(employee, codes):
    response = _verify(code="654321")

    assert response.status_code == 400
    assert response.json()["detail"] == "Codigo invalido o expirado"
    codes.claim_reset_attempt.assert_called_once()
    codes.reset_password_with_code.assert_not_called()


def test_verify_without_a_live_code(employee, codes):
    codes.claim_reset_attempt.return_value = None

    response = _verify()

    assert response.status_code == 400
    codes.reset_password_with_code.assert_not_called()


def test_verify_for_an_unknown_email_gives_the_same_answer(employee, codes):
    employee.return_value = None

    response = _verify(email="nadie@cen.com")

    assert response.status_code == 400
    assert response.json()["detail"] == "Codigo invalido o expirado"
    codes.claim_reset_attempt.assert_not_called()


def test_verify_loses_the_race_for_the_same_code(employee, codes):
    codes.reset_password_with_code.return_value = False

    response = _verify()

    assert response.status_code == 400


@pytest.mark.parametrize("code", ["12345", "1234567", "12a456", ""])
def test_verify_only_takes_six_digits(code, employee, codes):
    response = _verify(code=code)

    assert response.status_code == 422
    codes.claim_reset_attempt.assert_not_called()


def test_verify_needs_the_email(codes):
    response = client.post("/auth/password-reset/verify", json={
        "code": "123456", "new_password": "nuevaClave1",
    })

    assert response.status_code == 422


def test_verify_is_limited_by_address(employee, codes, rate_limit_window):
    rate_limit_window.return_value = {"hits": 11, "retry_after": 60}

    response = _verify()

    assert response.status_code == 429
    codes.claim_reset_attempt.assert_not_called()
    assert rate_limit_window.call_args[0][0] == "password-reset-verify"
