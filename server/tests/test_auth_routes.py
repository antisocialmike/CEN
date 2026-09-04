from unittest.mock import patch
from fastapi.testclient import TestClient
from passlib.context import CryptContext

from server.src.main import app

client = TestClient(app)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@patch("server.src.routes.auth_routes.payroll_repository.get_employee_by_email")
def test_login_success(mock_get_employee):
    mock_get_employee.return_value = {
        "id": 1,
        "email": "admin@cen.com",
        "role": "admin",
        "password_hash": pwd_context.hash("clave123")
    }

    response = client.post(
        "/auth/login",
        json={"email": "admin@cen.com", "password": "clave123"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "admin"
    assert body["token_type"] == "bearer"
    assert body["access_token"]


@patch("server.src.routes.auth_routes.payroll_repository.get_employee_by_email")
def test_login_wrong_password(mock_get_employee):
    mock_get_employee.return_value = {
        "id": 1,
        "email": "admin@cen.com",
        "role": "admin",
        "password_hash": pwd_context.hash("clave123")
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
