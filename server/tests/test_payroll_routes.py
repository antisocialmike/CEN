from datetime import date, datetime
from unittest.mock import patch

from fastapi.testclient import TestClient
from psycopg2 import OperationalError

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
    mock_save_receipt.return_value = {"id": 55, "created": True}

    response = client.post(
        "/payroll/calculate",
        json={"employee_id": 1, "period": "2026-09", "gross_salary": 10000},
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["receipt_id"] == 55
    assert body["created"] is True
    assert body["period"] == "2026-09"
    assert body["employee_id"] == 1
    assert body["data"]["net_salary"] == 9569.7
    assert body["processed_by"] == "admin1"
    saved = mock_save_receipt.call_args[0][0]
    assert saved["period"] == date(2026, 9, 1)
    assert saved["processed_by"] == "admin1"


@patch("server.src.routes.payroll_routes.payroll_repository.save_payroll_receipt")
@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_calculate_payroll_replacing_an_existing_period(mock_get_employee, mock_save):
    mock_get_employee.return_value = {"id": 1, "name": "Juan"}
    mock_save.return_value = {"id": 55, "created": False}

    response = client.post(
        "/payroll/calculate",
        json={"employee_id": 1, "period": "2026-09", "gross_salary": 10000},
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    assert response.json()["created"] is False


@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_calculate_payroll_rejects_a_malformed_period(mock_get_employee):
    mock_get_employee.return_value = {"id": 1, "name": "Juan"}

    response = client.post(
        "/payroll/calculate",
        json={"employee_id": 1, "period": "septiembre", "gross_salary": 10000},
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 422


@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_calculate_payroll_rejects_an_impossible_month(mock_get_employee):
    mock_get_employee.return_value = {"id": 1, "name": "Juan"}

    response = client.post(
        "/payroll/calculate",
        json={"employee_id": 1, "period": "2026-13", "gross_salary": 10000},
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 422


@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_calculate_payroll_employee_not_found(mock_get_employee):
    mock_get_employee.return_value = None

    response = client.post(
        "/payroll/calculate",
        json={"employee_id": 999, "period": "2026-09", "gross_salary": 10000},
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 404


@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_calculate_payroll_negative_salary(mock_get_employee):
    mock_get_employee.return_value = {"id": 1, "name": "Juan"}

    response = client.post(
        "/payroll/calculate",
        json={"employee_id": 1, "period": "2026-09", "gross_salary": -500},
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 400


def test_calculate_payroll_requires_admin_role():
    response = client.post(
        "/payroll/calculate",
        json={"employee_id": 1, "period": "2026-09", "gross_salary": 10000},
        headers={"Authorization": f"Bearer {_employee_token()}"}
    )

    assert response.status_code == 403


def test_calculate_payroll_requires_authentication():
    response = client.post(
        "/payroll/calculate",
        json={"employee_id": 1, "period": "2026-09", "gross_salary": 10000}
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


@patch("server.src.routes.payroll_routes.payroll_repository.list_recent_receipts")
def test_list_recent_receipts_success(mock_list_receipts):
    mock_list_receipts.return_value = [
        {
            "id": 1, "employee_id": 7, "employee_name": "Ana Lopez",
            "gross_salary": 10000.0, "isr_deduction": 192.8,
            "imss_deduction": 237.5, "net_salary": 9569.7,
            "created_at": "2026-09-01T10:00:00"
        }
    ]

    response = client.get(
        "/payroll/receipts",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    assert len(response.json()["receipts"]) == 1
    mock_list_receipts.assert_called_once_with(20)


def test_list_recent_receipts_requires_admin_role():
    response = client.get(
        "/payroll/receipts",
        headers={"Authorization": f"Bearer {_employee_token()}"}
    )

    assert response.status_code == 403


@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_unavailable_database_answers_503(mock_get_employee):
    mock_get_employee.side_effect = OperationalError("conexion rechazada")

    response = client.post(
        "/payroll/calculate",
        json={"employee_id": 1, "period": "2026-09", "gross_salary": 10000},
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Base de datos no disponible"


def test_lifespan_prepares_the_database_and_closes_the_pool():
    with patch("server.src.main.bootstrap_database") as mock_bootstrap, \
            patch("server.src.main.close_pool") as mock_close_pool:
        with TestClient(app):
            pass

    mock_bootstrap.assert_called_once()
    mock_close_pool.assert_called_once()


@patch("server.src.routes.payroll_routes.payroll_repository.save_payroll_receipt")
@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_calculate_payroll_rejects_a_deactivated_employee(mock_get_employee, mock_save):
    mock_get_employee.return_value = {"id": 3, "name": "Ana", "is_active": False}

    response = client.post(
        "/payroll/calculate",
        json={"employee_id": 3, "period": "2026-09", "gross_salary": 10000},
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 400
    assert "desactivada" in response.json()["detail"]
    mock_save.assert_not_called()


def _receipt_row(employee_id=7):
    return {
        "id": 42,
        "employee_id": employee_id,
        "employee_name": "Ana Lopez",
        "employee_email": "ana@cen.com",
        "period": date(2026, 9, 1),
        "gross_salary": 21000,
        "isr_deduction": 2612.86,
        "imss_deduction": 583.0,
        "net_salary": 17804.14,
        "processed_by": "admin@cen.com",
        "created_at": datetime(2026, 9, 8, 10, 30)
    }


@patch("server.src.routes.payroll_routes.payroll_repository.get_receipt_by_id")
def test_download_receipt_as_its_owner(mock_get_receipt):
    mock_get_receipt.return_value = _receipt_row(employee_id=7)

    response = client.get(
        "/payroll/receipts/42/pdf",
        headers={"Authorization": f"Bearer {_employee_token(employee_id=7)}"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "recibo-42-2026-09.pdf" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-")


@patch("server.src.routes.payroll_routes.payroll_repository.get_receipt_by_id")
def test_download_receipt_as_admin_for_anyone(mock_get_receipt):
    mock_get_receipt.return_value = _receipt_row(employee_id=99)

    response = client.get(
        "/payroll/receipts/42/pdf",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF-")


@patch("server.src.routes.payroll_routes.payroll_repository.get_receipt_by_id")
def test_download_receipt_of_somebody_else(mock_get_receipt):
    mock_get_receipt.return_value = _receipt_row(employee_id=99)

    response = client.get(
        "/payroll/receipts/42/pdf",
        headers={"Authorization": f"Bearer {_employee_token(employee_id=7)}"}
    )

    assert response.status_code == 403


@patch("server.src.routes.payroll_routes.payroll_repository.get_receipt_by_id")
def test_download_receipt_that_does_not_exist(mock_get_receipt):
    mock_get_receipt.return_value = None

    response = client.get(
        "/payroll/receipts/999/pdf",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 404


def test_download_receipt_requires_authentication():
    response = client.get("/payroll/receipts/42/pdf")

    assert response.status_code == 401


@patch("server.src.routes.payroll_routes.payroll_repository.save_payroll_receipt")
@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_calculate_payroll_with_every_concept(mock_get_employee, mock_save):
    mock_get_employee.return_value = {"id": 1, "name": "Juan", "is_active": True}
    mock_save.return_value = {"id": 55, "created": True}

    response = client.post(
        "/payroll/calculate",
        json={
            "employee_id": 1, "period": "2026-12", "gross_salary": 21000,
            "overtime_double_hours": 9, "overtime_triple_hours": 3,
            "christmas_bonus_days": 15, "vacation_days": 12,
            "bonus": 1500, "loan_deduction": 800,
            "housing_credit_deduction": 1200
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    data = response.json()["data"]
    conceptos = [item["concept"] for item in data["items"]]
    assert conceptos == [
        "sueldo", "horas_extra", "aguinaldo", "prima_vacacional", "bono",
        "isr", "imss", "prestamo", "infonavit"
    ]
    assert data["net_salary"] == round(
        data["total_perceptions"] - data["total_deductions"], 2
    )

    saved = mock_save.call_args[0][0]
    assert len(saved["items"]) == 9
    assert saved["total_perceptions"] == data["total_perceptions"]


@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_calculate_payroll_rejects_negative_concepts(mock_get_employee):
    mock_get_employee.return_value = {"id": 1, "name": "Juan", "is_active": True}

    response = client.post(
        "/payroll/calculate",
        json={
            "employee_id": 1, "period": "2026-12", "gross_salary": 21000,
            "loan_deduction": -500
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 422


@patch("server.src.routes.payroll_routes.payroll_repository.save_payroll_receipt")
@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_calculate_payroll_without_concepts_keeps_the_simple_shape(
    mock_get_employee, mock_save
):
    mock_get_employee.return_value = {"id": 1, "name": "Juan", "is_active": True}
    mock_save.return_value = {"id": 55, "created": True}

    response = client.post(
        "/payroll/calculate",
        json={"employee_id": 1, "period": "2026-09", "gross_salary": 10000},
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    data = response.json()["data"]
    assert [item["concept"] for item in data["items"]] == [
        "sueldo", "isr", "imss"
    ]
    assert data["net_salary"] == 9569.7
