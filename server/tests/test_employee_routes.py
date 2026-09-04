from unittest.mock import patch
from psycopg2 import errors as psycopg2_errors
from fastapi.testclient import TestClient

from server.src.main import app
from server.src.middlewares.auth_middleware import create_access_token

client = TestClient(app)


def _admin_token():
    return create_access_token(data={"sub": "admin1", "role": "admin"})


def _employee_token():
    return create_access_token(data={"sub": "empleado1", "role": "employee"})


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
