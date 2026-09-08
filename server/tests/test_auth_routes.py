from unittest.mock import patch

from fastapi.testclient import TestClient

from server.src.main import app
from server.src.middlewares.auth_middleware import create_access_token, hash_password

client = TestClient(app)


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
