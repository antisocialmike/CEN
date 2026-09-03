from unittest.mock import patch
from fastapi.testclient import TestClient

from server.src.main import app
from server.src.middlewares.auth_middleware import create_access_token

client = TestClient(app)


def _admin_token():
    return create_access_token(data={"sub": "admin1", "role": "admin"})


def _employee_token(employee_id=None):
    data = {"sub": "empleado1", "role": "employee"}
    if employee_id is not None:
        data["employee_id"] = employee_id
    return create_access_token(data=data)


@patch("server.src.routes.payroll_routes.payroll_repository.save_payroll_receipt")
@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_calculate_payroll_success(mock_get_employee, mock_save_receipt):
    mock_get_employee.return_value = {"id": 1, "name": "Juan"}
    mock_save_receipt.return_value = 55

    response = client.post(
        "/payroll/calculate",
        json={"employee_id": 1, "gross_salary": 10000},
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["receipt_id"] == 55
    assert body["employee_id"] == 1
    assert body["data"]["net_salary"] == 8125.0
    assert body["processed_by"] == "admin1"
    mock_save_receipt.assert_called_once()


@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_calculate_payroll_employee_not_found(mock_get_employee):
    mock_get_employee.return_value = None

    response = client.post(
        "/payroll/calculate",
        json={"employee_id": 999, "gross_salary": 10000},
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 404


@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_calculate_payroll_negative_salary(mock_get_employee):
    mock_get_employee.return_value = {"id": 1, "name": "Juan"}

    response = client.post(
        "/payroll/calculate",
        json={"employee_id": 1, "gross_salary": -500},
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 400


def test_calculate_payroll_requires_admin_role():
    response = client.post(
        "/payroll/calculate",
        json={"employee_id": 1, "gross_salary": 10000},
        headers={"Authorization": f"Bearer {_employee_token()}"}
    )

    assert response.status_code == 403


def test_calculate_payroll_requires_authentication():
    response = client.post(
        "/payroll/calculate",
        json={"employee_id": 1, "gross_salary": 10000}
    )

    assert response.status_code == 401


@patch("server.src.routes.payroll_routes.payroll_repository.get_receipts_by_employee_id")
def test_get_my_receipts_success(mock_get_receipts):
    mock_get_receipts.return_value = [
        {
            "id": 1, "employee_id": 7, "gross_salary": 10000.0,
            "isr_deduction": 1600.0, "imss_deduction": 275.0,
            "net_salary": 8125.0, "created_at": "2026-09-01T10:00:00"
        }
    ]

    response = client.get(
        "/payroll/my-receipts",
        headers={"Authorization": f"Bearer {_employee_token(employee_id=7)}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["employee_id"] == 7
    assert len(body["receipts"]) == 1
    mock_get_receipts.assert_called_once_with(7)


def test_get_my_receipts_token_without_employee_id():
    response = client.get(
        "/payroll/my-receipts",
        headers={"Authorization": f"Bearer {_employee_token()}"}
    )

    assert response.status_code == 403


def test_get_my_receipts_requires_authentication():
    response = client.get("/payroll/my-receipts")

    assert response.status_code == 401


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
