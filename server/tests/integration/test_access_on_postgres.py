import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from server.src.main import app
from server.src.middlewares.auth_middleware import (
    hash_password,
    hash_reset_code,
)
from server.src.repositories.auth_repository import AuthRepository
from server.src.repositories.payroll_repository import payroll_repository
from server.tests.integration.conftest import unique_email

client = TestClient(app)
repository = AuthRepository()


def _new_employee(email=None) -> int:
    return payroll_repository.create_employee({
        "name": "Ana", "email": email or unique_email("ana"),
        "role": "employee", "base_salary": 10000,
        "password_hash": hash_password("claveVieja1"),
    }, payroll_repository.first_company_id())


@pytest.fixture
def employee_id():
    return _new_employee()


def test_session_state_tells_the_role_and_the_version(employee_id):
    state = repository.session_state(employee_id, "employee")

    assert state["same_role"] is True
    assert state["is_active"] is True
    assert state["token_version"] == 0
    assert state["company_is_active"] is True
    assert repository.session_state(employee_id, "admin")["same_role"] is False


def test_changing_the_password_moves_the_session_version(employee_id):
    payroll_repository.update_password(employee_id, hash_password("otraClave1"))

    assert repository.session_state(employee_id, "employee")["token_version"] == 1


def test_a_reset_code_is_redeemed_only_once(employee_id):
    assert repository.issue_reset_code(
        employee_id, hash_reset_code("123456"), 15, 60, 5
    ) is True

    claimed = repository.claim_reset_attempt(employee_id, 5)
    assert claimed["code_hash"] == hash_reset_code("123456")
    assert repository.reset_password_with_code(
        claimed["id"], employee_id, hash_password("nuevaClave1")
    ) is True
    assert repository.reset_password_with_code(
        claimed["id"], employee_id, hash_password("otraMas1")
    ) is False
    assert repository.claim_reset_attempt(employee_id, 5) is None

    state = repository.session_state(employee_id, "employee")
    assert state["token_version"] == 1
    assert state["must_change_password"] is False


def test_a_second_request_inside_the_cooldown_is_ignored(employee_id):
    assert repository.issue_reset_code(employee_id, "a" * 64, 15, 60, 5) is True
    assert repository.issue_reset_code(employee_id, "b" * 64, 15, 60, 5) is False


def test_a_new_code_voids_the_previous_one(employee_id):
    repository.issue_reset_code(employee_id, "a" * 64, 15, 0, 5)
    repository.issue_reset_code(employee_id, "b" * 64, 15, 0, 5)

    assert repository.claim_reset_attempt(employee_id, 5)["code_hash"] == "b" * 64


def test_the_attempts_of_a_code_run_out(employee_id):
    repository.issue_reset_code(employee_id, "a" * 64, 15, 0, 5)

    for _ in range(5):
        assert repository.claim_reset_attempt(employee_id, 5) is not None
    assert repository.claim_reset_attempt(employee_id, 5) is None


def test_an_account_asks_for_a_few_codes_per_hour(employee_id):
    for letter in "abcde":
        assert repository.issue_reset_code(
            employee_id, letter * 64, 15, 0, 5
        ) is True

    assert repository.issue_reset_code(employee_id, "f" * 64, 15, 0, 5) is False


def test_the_address_limit_counts_inside_the_window():
    address = uuid.uuid4().hex

    assert repository.hit_rate_limit("login", address, 900)["hits"] == 1
    second = repository.hit_rate_limit("login", address, 900)

    assert second["hits"] == 2
    assert 0 < second["retry_after"] <= 900


def test_the_whole_recovery_by_email_ends_in_a_login():
    email = unique_email("recupera")
    _new_employee(email)

    with patch("server.src.routes.auth_routes.send_password_reset_email") as mail:
        requested = client.post(
            "/auth/password-reset/request", json={"email": email}
        )
    code = mail.call_args.kwargs["code"]
    wrong = "000000" if code != "000000" else "111111"

    rejected = client.post("/auth/password-reset/verify", json={
        "email": email, "code": wrong, "new_password": "nuevaClave1",
    })
    accepted = client.post("/auth/password-reset/verify", json={
        "email": email, "code": code, "new_password": "nuevaClave1",
    })
    login = client.post(
        "/auth/login", json={"email": email, "password": "nuevaClave1"}
    )

    assert requested.status_code == 204
    assert rejected.status_code == 400
    assert accepted.status_code == 204
    assert login.status_code == 200, login.text
