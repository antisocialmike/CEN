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


def _admin_token_with_id(employee_id=1):
    return create_access_token(
        data={"sub": "admin1", "role": "admin", "employee_id": employee_id}
    )


def _updated_payload():
    return {
        "name": "Ana Lopez",
        "email": "ana@cen.com",
        "role": "employee",
        "base_salary": 19000
    }


@patch("server.src.routes.employee_routes.payroll_repository.update_employee")
def test_update_employee_success(mock_update):
    mock_update.return_value = {
        "id": 3, "name": "Ana Lopez", "email": "ana@cen.com",
        "role": "employee", "base_salary": 19000, "is_active": True
    }

    response = client.put(
        "/employees/3",
        json=_updated_payload(),
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    assert response.json()["base_salary"] == 19000
    assert mock_update.call_args[0][0] == 3


@patch("server.src.routes.employee_routes.payroll_repository.update_employee")
def test_update_employee_not_found(mock_update):
    mock_update.return_value = None

    response = client.put(
        "/employees/999",
        json=_updated_payload(),
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 404


@patch("server.src.routes.employee_routes.payroll_repository.update_employee")
def test_update_employee_cannot_drop_your_own_admin_role(mock_update):
    response = client.put(
        "/employees/1",
        json=_updated_payload(),
        headers={"Authorization": f"Bearer {_admin_token_with_id(1)}"}
    )

    assert response.status_code == 400
    mock_update.assert_not_called()


@patch("server.src.routes.employee_routes.payroll_repository.update_employee")
def test_update_employee_can_keep_your_own_admin_role(mock_update):
    mock_update.return_value = {
        "id": 1, "name": "Admin", "email": "admin@cen.com",
        "role": "admin", "base_salary": 20000, "is_active": True
    }

    response = client.put(
        "/employees/1",
        json={**_updated_payload(), "role": "admin"},
        headers={"Authorization": f"Bearer {_admin_token_with_id(1)}"}
    )

    assert response.status_code == 200
    mock_update.assert_called_once()


def test_update_employee_requires_admin_role():
    response = client.put(
        "/employees/3",
        json=_updated_payload(),
        headers={"Authorization": f"Bearer {_employee_token()}"}
    )

    assert response.status_code == 403


@patch("server.src.routes.employee_routes.payroll_repository.set_employee_active")
def test_deactivate_employee_success(mock_set_active):
    mock_set_active.return_value = {
        "id": 3, "name": "Ana Lopez", "email": "ana@cen.com",
        "role": "employee", "base_salary": 19000, "is_active": False
    }

    response = client.post(
        "/employees/3/deactivate",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert mock_set_active.call_args[0] == (3, False)


@patch("server.src.routes.employee_routes.payroll_repository.set_employee_active")
def test_deactivate_employee_cannot_be_yourself(mock_set_active):
    response = client.post(
        "/employees/1/deactivate",
        headers={"Authorization": f"Bearer {_admin_token_with_id(1)}"}
    )

    assert response.status_code == 400
    mock_set_active.assert_not_called()


@patch("server.src.routes.employee_routes.payroll_repository.set_employee_active")
def test_deactivate_employee_not_found(mock_set_active):
    mock_set_active.return_value = None

    response = client.post(
        "/employees/999/deactivate",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 404


@patch("server.src.routes.employee_routes.payroll_repository.set_employee_active")
def test_activate_employee_success(mock_set_active):
    mock_set_active.return_value = {
        "id": 3, "name": "Ana Lopez", "email": "ana@cen.com",
        "role": "employee", "base_salary": 19000, "is_active": True
    }

    response = client.post(
        "/employees/3/activate",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is True
    assert mock_set_active.call_args[0] == (3, True)


def test_activate_employee_requires_admin_role():
    response = client.post(
        "/employees/3/activate",
        headers={"Authorization": f"Bearer {_employee_token()}"}
    )

    assert response.status_code == 403


@patch("server.src.routes.employee_routes.payroll_repository.set_employee_active")
def test_activate_employee_not_found(mock_set_active):
    mock_set_active.return_value = None

    response = client.post(
        "/employees/999/activate",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 404


@patch("server.src.routes.employee_routes.payroll_repository.reset_password")
def test_reset_password_returns_a_temporary_one(mock_reset):
    mock_reset.return_value = {
        "id": 3, "name": "Ana Lopez", "email": "ana@cen.com",
        "role": "employee", "base_salary": 19000, "is_active": True
    }

    response = client.post(
        "/employees/3/reset-password",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["employee_id"] == 3
    assert len(body["temporary_password"]) >= 8

    employee_id, password_hash = mock_reset.call_args[0]
    assert employee_id == 3
    assert password_hash != body["temporary_password"]
    assert password_hash.startswith("$2b$")


@patch("server.src.routes.employee_routes.payroll_repository.reset_password")
def test_reset_password_gives_a_different_one_each_time(mock_reset):
    mock_reset.return_value = {
        "id": 3, "name": "Ana Lopez", "email": "ana@cen.com",
        "role": "employee", "base_salary": 19000, "is_active": True
    }
    headers = {"Authorization": f"Bearer {_admin_token()}"}

    first = client.post("/employees/3/reset-password", headers=headers).json()
    second = client.post("/employees/3/reset-password", headers=headers).json()

    assert first["temporary_password"] != second["temporary_password"]


@patch("server.src.routes.employee_routes.payroll_repository.reset_password")
def test_reset_password_for_a_missing_employee(mock_reset):
    mock_reset.return_value = None

    response = client.post(
        "/employees/999/reset-password",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 404


@patch("server.src.routes.employee_routes.payroll_repository.reset_password")
def test_reset_password_cannot_be_yourself(mock_reset):
    response = client.post(
        "/employees/1/reset-password",
        headers={"Authorization": f"Bearer {_admin_token_with_id(1)}"}
    )

    assert response.status_code == 400
    mock_reset.assert_not_called()


def test_reset_password_requires_admin_role():
    response = client.post(
        "/employees/3/reset-password",
        headers={"Authorization": f"Bearer {_employee_token()}"}
    )

    assert response.status_code == 403
