from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from psycopg2 import OperationalError

from server.src.main import app
from server.src.middlewares.auth_middleware import create_access_token
from server.tests.payroll_parameters import ISR_2026, PAYROLL_ONLY_RATES_2026

client = TestClient(app)

ADMIN_COMPANY_ID = 1


@pytest.fixture(autouse=True)
def admin_company():
    # El admin de estas pruebas administra una sola empresa, la 1. Las
    # pruebas de aislamiento entre empresas viven en test_company_isolation.
    with patch(
        "server.src.middlewares.company_context.company_repository"
    ) as repository:
        repository.admin_company_ids.return_value = [ADMIN_COMPANY_ID]
        repository.admin_has_company.return_value = True
        yield repository


@pytest.fixture(autouse=True)
def payroll_parameters_only():
    # Los parametros del calculo de 2026, sin los del costo patronal: ese queda
    # pendiente; sus cifras se prueban en test_employer_cost y en
    # test_employer_cost_routes.
    with patch(
        "server.src.routes.payroll_routes.payroll_repository"
        ".employer_cost_parameters",
        return_value={
            "rates": PAYROLL_ONLY_RATES_2026, "ceav_brackets": [],
            "isn_rate": None, "risk_rate": None,
        },
    ), patch(
        "server.src.routes.payroll_routes.payroll_repository.isr_brackets",
        return_value=ISR_2026,
    ):
        yield


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
        json={
            "employee_id": 1, "periodicity": "mensual",
            "period_start": "2026-09-01", "gross_salary": 10000
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["receipt_id"] == 55
    assert body["created"] is True
    assert body["period_start"] == "2026-09-01"
    assert body["period_end"] == "2026-09-30"
    assert body["employee_id"] == 1
    # 10,000 - 193.37 de ISR - 249.21 de IMSS sobre el SBC (30 dias de septiembre).
    assert body["data"]["net_salary"] == 9557.42
    assert body["processed_by"] == "admin1"
    saved = mock_save_receipt.call_args[0][0]
    assert saved["period_start"] == date(2026, 9, 1)
    assert saved["processed_by"] == "admin1"


@patch("server.src.routes.payroll_routes.payroll_repository.save_payroll_receipt")
@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_calculate_payroll_replacing_an_existing_period(mock_get_employee, mock_save):
    mock_get_employee.return_value = {"id": 1, "name": "Juan"}
    mock_save.return_value = {"id": 55, "created": False}

    response = client.post(
        "/payroll/calculate",
        json={
            "employee_id": 1, "periodicity": "mensual",
            "period_start": "2026-09-01", "gross_salary": 10000
        },
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
        json={
            "employee_id": 1, "periodicity": "mensual",
            "period_start": "2026-13-01", "gross_salary": 10000
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 422


@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_calculate_payroll_employee_not_found(mock_get_employee):
    mock_get_employee.return_value = None

    response = client.post(
        "/payroll/calculate",
        json={
            "employee_id": 999, "periodicity": "mensual",
            "period_start": "2026-09-01", "gross_salary": 10000
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 404


@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_calculate_payroll_negative_salary(mock_get_employee):
    mock_get_employee.return_value = {"id": 1, "name": "Juan"}

    response = client.post(
        "/payroll/calculate",
        json={
            "employee_id": 1, "periodicity": "mensual",
            "period_start": "2026-09-01", "gross_salary": -500
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 400


def test_calculate_payroll_requires_admin_role():
    response = client.post(
        "/payroll/calculate",
        json={
            "employee_id": 1, "periodicity": "mensual",
            "period_start": "2026-09-01", "gross_salary": 10000
        },
        headers={"Authorization": f"Bearer {_employee_token()}"}
    )

    assert response.status_code == 403


def test_calculate_payroll_requires_authentication():
    response = client.post(
        "/payroll/calculate",
        json={
            "employee_id": 1, "periodicity": "mensual",
            "period_start": "2026-09-01", "gross_salary": 10000
        }
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


@patch("server.src.main.database_ready", return_value=True)
def test_health_check(mock_ready):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("server.src.main.database_ready", return_value=False)
def test_health_check_fails_without_database(mock_ready):
    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["detail"] == "Base de datos no disponible"


@patch("server.src.routes.payroll_routes.payroll_repository.page_receipts")
def test_list_receipts_starts_on_the_first_page(mock_page_receipts):
    mock_page_receipts.return_value = ([
        {
            "id": 1, "employee_id": 7, "employee_name": "Ana Lopez",
            "gross_salary": 10000.0, "isr_deduction": 192.8,
            "imss_deduction": 237.5, "net_salary": 9569.7,
            "created_at": "2026-09-01T10:00:00"
        }
    ], 41)

    response = client.get(
        "/payroll/receipts",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert (body["total"], body["page"], body["page_size"]) == (41, 1, 20)
    mock_page_receipts.assert_called_once_with(ADMIN_COMPANY_ID, 20, 0)


@patch("server.src.routes.payroll_routes.payroll_repository.page_receipts")
def test_list_receipts_skips_the_previous_pages(mock_page_receipts):
    mock_page_receipts.return_value = ([], 41)

    response = client.get(
        "/payroll/receipts?page=3&page_size=10",
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    mock_page_receipts.assert_called_once_with(ADMIN_COMPANY_ID, 10, 20)


@pytest.mark.parametrize("query", [
    "page=0", "page=-1", "page=uno", "page_size=0", "page_size=101",
])
@patch("server.src.routes.payroll_routes.payroll_repository.page_receipts")
def test_list_receipts_rejects_impossible_pages(mock_page_receipts, query):
    response = client.get(
        "/payroll/receipts?" + query,
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 422
    mock_page_receipts.assert_not_called()


def test_list_receipts_requires_admin_role():
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
        json={
            "employee_id": 1, "periodicity": "mensual",
            "period_start": "2026-09-01", "gross_salary": 10000
        },
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
        json={
            "employee_id": 3, "periodicity": "mensual",
            "period_start": "2026-09-01", "gross_salary": 10000
        },
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
        "company_id": ADMIN_COMPANY_ID,
        "period_start": date(2026, 9, 1),
        "period_end": date(2026, 9, 30),
        "periodicity": "mensual",
        "paid_days": 30,
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
    assert "recibo-42-2026-09-01.pdf" in response.headers["content-disposition"]
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
            "employee_id": 1, "periodicity": "mensual",
            "period_start": "2026-12-01", "gross_salary": 21000,
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
            "employee_id": 1, "periodicity": "mensual",
            "period_start": "2026-12-01", "gross_salary": 21000,
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
        json={
            "employee_id": 1, "periodicity": "mensual",
            "period_start": "2026-09-01", "gross_salary": 10000
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    data = response.json()["data"]
    assert [item["concept"] for item in data["items"]] == [
        "sueldo", "isr", "imss"
    ]
    assert data["net_salary"] == 9557.42


@patch("server.src.routes.payroll_routes.payroll_repository.get_receipt_by_period")
def test_lookup_finds_an_existing_receipt(mock_lookup):
    mock_lookup.return_value = {
        "id": 12, "employee_id": 3, "period_start": date(2026, 9, 1),
        "period_end": date(2026, 9, 30), "periodicity": "mensual",
        "net_salary": 17862.79, "processed_by": "admin@cen.com"
    }

    response = client.post(
        "/payroll/lookup",
        json={
            "employee_id": 3, "periodicity": "mensual",
            "period_start": "2026-09-01"
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    assert response.json()["receipt"]["id"] == 12
    assert mock_lookup.call_args[0] == (
        3, date(2026, 9, 1), date(2026, 9, 30), ADMIN_COMPANY_ID
    )


@patch("server.src.routes.payroll_routes.payroll_repository.get_receipt_by_period")
def test_lookup_returns_null_when_the_period_is_free(mock_lookup):
    mock_lookup.return_value = None

    response = client.post(
        "/payroll/lookup",
        json={
            "employee_id": 3, "periodicity": "quincenal",
            "period_start": "2026-09-16"
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    assert response.json()["receipt"] is None


@patch("server.src.routes.payroll_routes.payroll_repository.get_receipt_by_period")
def test_lookup_resolves_the_second_fortnight(mock_lookup):
    mock_lookup.return_value = None

    client.post(
        "/payroll/lookup",
        json={
            "employee_id": 3, "periodicity": "quincenal",
            "period_start": "2026-01-16"
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert mock_lookup.call_args[0][2] == date(2026, 1, 31)


def test_lookup_rejects_an_invalid_period_start():
    response = client.post(
        "/payroll/lookup",
        json={
            "employee_id": 3, "periodicity": "quincenal",
            "period_start": "2026-01-10"
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 422


def test_lookup_requires_admin_role():
    response = client.post(
        "/payroll/lookup",
        json={
            "employee_id": 3, "periodicity": "mensual",
            "period_start": "2026-09-01"
        },
        headers={"Authorization": f"Bearer {_employee_token()}"}
    )

    assert response.status_code == 403


@patch("server.src.routes.payroll_routes.payroll_repository.save_payroll_receipt")
@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_a_period_without_parameters_in_force_is_not_calculated(
    mock_get_employee, mock_save
):
    mock_get_employee.return_value = {"id": 1, "name": "Juan", "is_active": True}

    with patch(
        "server.src.routes.payroll_routes.payroll_repository.isr_brackets",
        return_value=[],
    ):
        response = client.post(
            "/payroll/calculate",
            json={
                "employee_id": 1, "periodicity": "mensual",
                "period_start": "2024-09-01", "gross_salary": 10000
            },
            headers={"Authorization": f"Bearer {_admin_token()}"}
        )

    assert response.status_code == 422
    assert "2024-09-01" in response.json()["detail"]
    assert "la tarifa del ISR" in response.json()["detail"]
    mock_save.assert_not_called()


@patch("server.src.routes.payroll_routes.payroll_repository.save_payroll_receipt")
@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_the_parameters_are_the_ones_in_force_when_the_period_starts(
    mock_get_employee, mock_save
):
    mock_get_employee.return_value = {"id": 1, "name": "Juan", "is_active": True}
    mock_save.return_value = {"id": 55, "created": True}

    with patch(
        "server.src.routes.payroll_routes.payroll_repository.isr_brackets",
        return_value=ISR_2026,
    ) as mock_isr:
        client.post(
            "/payroll/calculate",
            json={
                "employee_id": 1, "periodicity": "quincenal",
                "period_start": "2026-01-16", "gross_salary": 5000
            },
            headers={"Authorization": f"Bearer {_admin_token()}"}
        )

    mock_isr.assert_called_once_with(date(2026, 1, 16))


@patch("server.src.routes.payroll_routes.payroll_repository.save_payroll_receipt")
@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_minimum_wage_retains_nothing_and_the_employer_pays_the_imss(
    mock_get_employee, mock_save
):
    mock_get_employee.return_value = {"id": 1, "name": "Juan", "is_active": True}
    mock_save.return_value = {"id": 55, "created": True}

    response = client.post(
        "/payroll/calculate",
        json={
            "employee_id": 1, "periodicity": "mensual",
            "period_start": "2026-09-01", "gross_salary": 9451.20
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    data = response.json()["data"]
    assert (data["isr_deduction"], data["imss_deduction"]) == (0.0, 0.0)
    assert data["net_salary"] == 9451.20
    employer_cost = mock_save.call_args[0][0]["employer_cost"]
    quota = next(
        item for item in employer_cost["items"]
        if item["component"] == "imss_obrero_patron"
    )
    assert quota["amount"] == Decimal("235.54")


@patch("server.src.routes.payroll_routes.payroll_repository.save_payroll_receipt")
@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_an_assimilated_is_calculated_without_imss_nor_subsidy(
    mock_get_employee, mock_save
):
    mock_get_employee.return_value = {
        "id": 1, "name": "Juan", "is_active": True, "tipo_regimen": "09",
    }
    mock_save.return_value = {"id": 55, "created": True}

    response = client.post(
        "/payroll/calculate",
        json={
            "employee_id": 1, "periodicity": "mensual",
            "period_start": "2026-09-01", "gross_salary": 10000
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert [item["concept"] for item in data["items"]] == ["sueldo", "isr"]
    assert data["isr_deduction"] == 729.02
    saved = mock_save.call_args[0][0]
    assert saved["tipo_regimen"] == "09"
    # Ni IMSS, ni SAR, ni INFONAVIT: solo puede quedar el ISN, aqui pendiente.
    assert [
        item for item in saved["employer_cost"]["items"]
        if item["group_key"] in ("imss", "sar", "infonavit")
    ] == []
    assert saved["employer_cost"]["sbc_daily"] is None


@patch("server.src.routes.payroll_routes.payroll_repository.save_payroll_receipt")
@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_an_assimilated_cannot_get_overtime(mock_get_employee, mock_save):
    mock_get_employee.return_value = {
        "id": 1, "name": "Juan", "is_active": True, "tipo_regimen": "09",
    }

    response = client.post(
        "/payroll/calculate",
        json={
            "employee_id": 1, "periodicity": "mensual",
            "period_start": "2026-09-01", "gross_salary": 10000,
            "overtime_double_hours": 4
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    assert response.status_code == 400
    assert "asimilado" in response.json()["detail"]
    mock_save.assert_not_called()


@patch("server.src.routes.payroll_routes.payroll_repository.save_payroll_receipt")
@patch("server.src.routes.payroll_routes.payroll_repository.get_employee_by_id")
def test_the_overtime_uses_the_workday_of_the_person(mock_get_employee, mock_save):
    mock_get_employee.return_value = {
        "id": 1, "name": "Juan", "is_active": True,
        "tipo_regimen": "02", "tipo_jornada": "02",
    }
    mock_save.return_value = {"id": 55, "created": True}

    response = client.post(
        "/payroll/calculate",
        json={
            "employee_id": 1, "periodicity": "mensual",
            "period_start": "2026-09-01", "gross_salary": 21000,
            "overtime_double_hours": 9
        },
        headers={"Authorization": f"Bearer {_admin_token()}"}
    )

    horas = next(
        item for item in response.json()["data"]["items"]
        if item["concept"] == "horas_extra"
    )
    # Nocturna: 700 diarios / 7 horas = 100 la hora, x 2 x 9.
    assert horas["amount"] == 1800.0
