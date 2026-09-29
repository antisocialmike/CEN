from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from server.src.main import app
from server.src.middlewares.auth_middleware import create_access_token
from server.src.models.auth_model import LoginRequest, PasswordResetVerify
from server.src.models.payroll_model import EmployeeCreateRequest
from server.src.models.platform_model import AdminAssignRequest, OwnerCreateRequest
from server.src.repositories.payroll_repository import PayrollRepository

client = TestClient(app)


@pytest.mark.parametrize("model, data", [
    (LoginRequest, {"password": "x"}),
    (PasswordResetVerify, {"code": "123456", "new_password": "nuevaClave1"}),
    (OwnerCreateRequest, {"name": "Laura"}),
    (AdminAssignRequest, {}),
    (EmployeeCreateRequest, {
        "name": "Ana", "role": "employee", "base_salary": 1,
        "password": "clave1234",
    }),
])
def test_every_email_that_comes_in_is_trimmed_and_lowercased(model, data):
    request = model(email="  Ana.Lopez@CEN.com ", **data)

    assert request.email == "ana.lopez@cen.com"


def test_the_lookup_by_email_ignores_case():
    cursor = MagicMock()
    cursor.fetchone.return_value = None
    with patch(
        "server.src.repositories.payroll_repository.db_cursor"
    ) as db_cursor:
        db_cursor.return_value.__enter__.return_value = cursor
        PayrollRepository().get_employee_by_email(" Ana@CEN.com")

    assert cursor.execute.call_args[0][1] == ("ana@cen.com",)


@patch("server.src.routes.auth_routes.payroll_repository.get_employee_by_email")
def test_login_with_capital_letters_finds_the_account(mock_get_employee):
    mock_get_employee.return_value = None

    client.post("/auth/login", json={"email": "ANA@Cen.com", "password": "x"})

    mock_get_employee.assert_called_once_with("ana@cen.com")


@patch("server.src.routes.employee_routes.payroll_repository.create_employee")
def test_a_new_employee_is_saved_with_the_email_in_lowercase(mock_create):
    mock_create.return_value = 10
    token = create_access_token(
        data={"sub": "admin1", "role": "admin", "employee_id": 99}
    )

    with patch(
        "server.src.middlewares.company_context.company_repository"
    ) as companies:
        companies.admin_company_ids.return_value = [1]
        response = client.post("/employees", json={
            "name": "Ana", "email": "Ana@CEN.com", "role": "employee",
            "base_salary": 1, "password": "clave1234",
        }, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert mock_create.call_args[0][0]["email"] == "ana@cen.com"
    assert response.json()["email"] == "ana@cen.com"
