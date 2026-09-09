from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from server.src.main import app
from server.src.config.settings import LOGIN_LOCK_MINUTES, LOGIN_MAX_ATTEMPTS
from server.src.middlewares.auth_middleware import create_access_token, hash_password

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_login_counters():
    with patch(
        "server.src.routes.auth_routes.payroll_repository.clear_failed_logins"
    ), patch(
        "server.src.routes.auth_routes.payroll_repository.register_failed_login"
    ) as register:
        register.return_value = {"failed_login_attempts": 1, "locked_until": None}
        yield register


@patch("server.src.routes.auth_routes.payroll_repository.get_employee_by_email")
def test_login_success(mock_get_employee):
    mock_get_employee.return_value = {
        "id": 1,
        "email": "admin@cen.com",
        "role": "admin",
        "password_hash": hash_password("clave123"),
        "must_change_password": True
    }

    response = client.post(
        "/auth/login",
        json={"email": "admin@cen.com", "password": "clave123"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "admin"
    assert body["must_change_password"] is True
    assert body["token_type"] == "bearer"
    assert body["access_token"]


@patch("server.src.routes.auth_routes.payroll_repository.get_employee_by_email")
def test_login_wrong_password(mock_get_employee):
    mock_get_employee.return_value = {
        "id": 1,
        "email": "admin@cen.com",
        "role": "admin",
        "password_hash": hash_password("clave123")
    }

    response = client.post(
        "/auth/login",
        json={"email": "admin@cen.com", "password": "otra_clave"}
    )

    assert response.status_code == 401


@patch("server.src.routes.auth_routes.payroll_repository.get_employee_by_email")
def test_login_employee_not_found(mock_get_employee):
    mock_get_employee.return_value = None

    response = client.post(
        "/auth/login",
        json={"email": "nadie@cen.com", "password": "clave123"}
    )

    assert response.status_code == 401


def _token_for(employee_id=7):
    return create_access_token(
        data={"sub": "ana@cen.com", "role": "employee", "employee_id": employee_id}
    )


@patch("server.src.routes.auth_routes.payroll_repository.update_password")
@patch("server.src.routes.auth_routes.payroll_repository.get_password_hash")
def test_change_password_success(mock_get_hash, mock_update):
    mock_get_hash.return_value = hash_password("clave123")

    response = client.post(
        "/auth/password",
        json={"current_password": "clave123", "new_password": "nuevaClave1"},
        headers={"Authorization": f"Bearer {_token_for()}"}
    )

    assert response.status_code == 204
    mock_update.assert_called_once()
    employee_id, new_hash = mock_update.call_args[0]
    assert employee_id == 7
    assert new_hash != "nuevaClave1"


@patch("server.src.routes.auth_routes.payroll_repository.update_password")
@patch("server.src.routes.auth_routes.payroll_repository.get_password_hash")
def test_change_password_with_wrong_current_one(mock_get_hash, mock_update):
    mock_get_hash.return_value = hash_password("clave123")

    response = client.post(
        "/auth/password",
        json={"current_password": "otra_clave", "new_password": "nuevaClave1"},
        headers={"Authorization": f"Bearer {_token_for()}"}
    )

    assert response.status_code == 400
    mock_update.assert_not_called()


@patch("server.src.routes.auth_routes.payroll_repository.update_password")
@patch("server.src.routes.auth_routes.payroll_repository.get_password_hash")
def test_change_password_rejects_reusing_the_same_one(mock_get_hash, mock_update):
    mock_get_hash.return_value = hash_password("clave123")

    response = client.post(
        "/auth/password",
        json={"current_password": "clave123", "new_password": "clave123"},
        headers={"Authorization": f"Bearer {_token_for()}"}
    )

    assert response.status_code == 400
    mock_update.assert_not_called()


@patch("server.src.routes.auth_routes.payroll_repository.get_password_hash")
def test_change_password_for_a_deleted_employee(mock_get_hash):
    mock_get_hash.return_value = None

    response = client.post(
        "/auth/password",
        json={"current_password": "clave123", "new_password": "nuevaClave1"},
        headers={"Authorization": f"Bearer {_token_for()}"}
    )

    assert response.status_code == 400


def test_change_password_needs_an_employee_in_the_token():
    token = create_access_token(data={"sub": "admin1", "role": "admin"})

    response = client.post(
        "/auth/password",
        json={"current_password": "clave123", "new_password": "nuevaClave1"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


def test_change_password_rejects_a_short_new_one():
    response = client.post(
        "/auth/password",
        json={"current_password": "clave123", "new_password": "corta"},
        headers={"Authorization": f"Bearer {_token_for()}"}
    )

    assert response.status_code == 422


def test_change_password_requires_authentication():
    response = client.post(
        "/auth/password",
        json={"current_password": "clave123", "new_password": "nuevaClave1"}
    )

    assert response.status_code == 401


@patch("server.src.routes.auth_routes.payroll_repository.get_employee_by_email")
def test_login_rejects_a_deactivated_account(mock_get_employee):
    mock_get_employee.return_value = {
        "id": 3,
        "email": "ana@cen.com",
        "role": "employee",
        "password_hash": hash_password("clave123"),
        "is_active": False
    }

    response = client.post(
        "/auth/login",
        json={"email": "ana@cen.com", "password": "clave123"}
    )

    assert response.status_code == 403
    assert "desactivada" in response.json()["detail"]


@patch("server.src.routes.auth_routes.payroll_repository.get_employee_by_email")
def test_login_checks_the_password_before_the_account_state(mock_get_employee):
    mock_get_employee.return_value = {
        "id": 3,
        "email": "ana@cen.com",
        "role": "employee",
        "password_hash": hash_password("clave123"),
        "is_active": False
    }

    response = client.post(
        "/auth/login",
        json={"email": "ana@cen.com", "password": "equivocada"}
    )

    assert response.status_code == 401


def _locked(minutes=10):
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)


@patch("server.src.routes.auth_routes.payroll_repository.get_employee_by_email")
def test_login_blocked_while_the_account_is_locked(mock_get_employee):
    mock_get_employee.return_value = {
        "id": 1, "email": "ana@cen.com", "role": "employee",
        "password_hash": hash_password("clave123"),
        "is_active": True, "locked_until": _locked(10)
    }

    response = client.post(
        "/auth/login",
        json={"email": "ana@cen.com", "password": "clave123"}
    )

    assert response.status_code == 429
    assert "intentos fallidos" in response.json()["detail"]


@patch("server.src.routes.auth_routes.payroll_repository.get_employee_by_email")
def test_login_counts_every_failed_attempt(mock_get_employee, isolate_login_counters):
    mock_get_employee.return_value = {
        "id": 1, "email": "ana@cen.com", "role": "employee",
        "password_hash": hash_password("clave123"),
        "is_active": True, "locked_until": None
    }

    response = client.post(
        "/auth/login",
        json={"email": "ana@cen.com", "password": "equivocada"}
    )

    assert response.status_code == 401
    isolate_login_counters.assert_called_once()
    employee_id, max_attempts, lock_minutes = isolate_login_counters.call_args[0]
    assert employee_id == 1
    assert max_attempts == LOGIN_MAX_ATTEMPTS
    assert lock_minutes == LOGIN_LOCK_MINUTES


@patch("server.src.routes.auth_routes.payroll_repository.get_employee_by_email")
def test_login_locks_the_account_on_the_last_attempt(
    mock_get_employee, isolate_login_counters
):
    mock_get_employee.return_value = {
        "id": 1, "email": "ana@cen.com", "role": "employee",
        "password_hash": hash_password("clave123"),
        "is_active": True, "locked_until": None
    }
    isolate_login_counters.return_value = {
        "failed_login_attempts": LOGIN_MAX_ATTEMPTS,
        "locked_until": _locked(15)
    }

    response = client.post(
        "/auth/login",
        json={"email": "ana@cen.com", "password": "equivocada"}
    )

    assert response.status_code == 429


@patch("server.src.routes.auth_routes.payroll_repository.clear_failed_logins")
@patch("server.src.routes.auth_routes.payroll_repository.get_employee_by_email")
def test_login_clears_the_counter_on_success(mock_get_employee, mock_clear):
    mock_get_employee.return_value = {
        "id": 1, "email": "ana@cen.com", "role": "employee",
        "password_hash": hash_password("clave123"),
        "is_active": True, "locked_until": None
    }

    response = client.post(
        "/auth/login",
        json={"email": "ana@cen.com", "password": "clave123"}
    )

    assert response.status_code == 200
    mock_clear.assert_called_once_with(1)


@patch("server.src.routes.auth_routes.payroll_repository.get_employee_by_email")
def test_login_ignores_an_expired_lock(mock_get_employee, isolate_login_counters):
    mock_get_employee.return_value = {
        "id": 1, "email": "ana@cen.com", "role": "employee",
        "password_hash": hash_password("clave123"),
        "is_active": True, "locked_until": _locked(-30)
    }

    response = client.post(
        "/auth/login",
        json={"email": "ana@cen.com", "password": "clave123"}
    )

    assert response.status_code == 200
