from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from psycopg2 import errors as psycopg2_errors

from server.src.main import app
from server.src.middlewares.auth_middleware import create_access_token
from server.src.repositories.company_repository import CompanyRepository
from server.src.repositories.payroll_repository import PayrollRepository
from server.tests.payroll_parameters import (
    ISR_2026,
    PAYROLL_ONLY_RATES_2026,
    PAYROLL_RATES_2026,
)
from server.tests.test_employer_cost import CEAV_2026

client = TestClient(app)

PAYROLL = "server.src.routes.payroll_routes.payroll_repository"
CONTEXT = "server.src.middlewares.company_context.company_repository"
OWNER_ROUTES = "server.src.routes.owner_routes.company_repository"
COMPANY = 1


def _headers(role: str, employee_id: int) -> dict:
    token = create_access_token(data={
        "sub": role + "@cen.com", "role": role, "employee_id": employee_id,
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def company_context():
    with patch(CONTEXT) as context:
        context.admin_company_ids.return_value = [COMPANY]
        context.admin_has_company.return_value = True
        context.owner_has_company.side_effect = (
            lambda owner_id, company_id: company_id == COMPANY
        )
        yield context


# --- Calcular nomina guarda el costo patronal --------------------------------

@pytest.fixture(autouse=True)
def isr_2026():
    with patch(PAYROLL + ".isr_brackets", return_value=ISR_2026):
        yield


@patch(PAYROLL + ".save_payroll_receipt")
@patch(PAYROLL + ".employer_cost_parameters")
@patch(PAYROLL + ".get_employee_by_id")
def test_payroll_saves_its_employer_cost(mock_employee, mock_params, mock_save):
    mock_employee.return_value = {
        "id": 5, "name": "Ana", "is_active": True,
        "created_at": datetime(2026, 3, 1, tzinfo=timezone.utc),
    }
    mock_params.return_value = {
        "rates": PAYROLL_RATES_2026, "ceav_brackets": CEAV_2026,
        "isn_rate": Decimal("0.03"), "risk_rate": Decimal("0.0054355"),
    }
    mock_save.return_value = {"id": 9, "created": True}

    # Un mes de septiembre (30 dias) con el salario minimo: el caso calculado a
    # mano en test_employer_cost da 2,793.50, mas los 235.54 de la cuota obrera
    # que por ser salario minimo paga la empresa (LSS art. 36).
    response = client.post("/payroll/calculate", json={
        "employee_id": 5, "period_start": "2026-09-01", "gross_salary": 9451.20,
    }, headers=_headers("admin", 3))

    assert response.status_code == 200
    mock_params.assert_called_once_with(COMPANY, date(2026, 9, 1))
    saved = mock_save.call_args[0][0]["employer_cost"]
    assert saved["total"] == Decimal("3029.04")
    assert saved["sbc_daily"] == Decimal("330.58")
    assert saved["missing"] == []
    assert response.json()["employer_cost"]["total"] == 3029.04
    assert response.json()["data"]["imss_deduction"] == 0.0


@patch(PAYROLL + ".save_payroll_receipt")
@patch(PAYROLL + ".employer_cost_parameters")
@patch(PAYROLL + ".get_employee_by_id")
def test_payroll_without_parameters_still_saves(
    mock_employee, mock_params, mock_save
):
    mock_employee.return_value = {"id": 5, "name": "Ana", "is_active": True}
    # Estan los parametros del calculo, pero no las tasas del costo patronal.
    mock_params.return_value = {
        "rates": PAYROLL_ONLY_RATES_2026, "ceav_brackets": [],
        "isn_rate": None, "risk_rate": None,
    }
    mock_save.return_value = {"id": 9, "created": True}

    response = client.post("/payroll/calculate", json={
        "employee_id": 5, "period_start": "2026-09-01", "gross_salary": 20000,
    }, headers=_headers("admin", 3))

    assert response.status_code == 200
    employer_cost = mock_save.call_args[0][0]["employer_cost"]
    assert employer_cost["total"] == Decimal("0.00")
    assert "isn" in employer_cost["missing"]


# --- El repositorio -----------------------------------------------------------

@pytest.fixture
def cursor():
    with patch(
        "server.src.repositories.payroll_repository.db_cursor"
    ) as payroll_cursor, patch(
        "server.src.repositories.company_repository.db_cursor"
    ) as company_cursor:
        mock_cursor = MagicMock()
        payroll_cursor.return_value.__enter__.return_value = mock_cursor
        company_cursor.return_value.__enter__.return_value = mock_cursor
        yield mock_cursor


def _queries(cursor) -> list:
    return [str(call[0][0]) for call in cursor.execute.call_args_list]


def _receipt(employer_cost=None) -> dict:
    data = {
        "employee_id": 5, "company_id": COMPANY,
        "period_start": date(2026, 9, 1), "period_end": date(2026, 9, 30),
        "periodicity": "mensual", "paid_days": 30, "processed_by": "admin",
        "gross_salary": 9451.2, "isr_deduction": 0, "imss_deduction": 0,
        "net_salary": 9451.2, "total_perceptions": 9451.2,
        "total_deductions": 0, "taxable_base": 9451.2, "items": [],
    }
    if employer_cost is not None:
        data["employer_cost"] = employer_cost
    return data


EMPLOYER_COST = {
    "daily_salary": Decimal("315.04"), "integration_factor": Decimal("1.049315"),
    "sbc_daily": Decimal("330.58"), "uma_daily": Decimal("117.31"),
    "days": Decimal(30), "total": Decimal("1315.49"), "missing": ["isn"],
    "items": [
        {"component": "em_cuota_fija", "group_key": "imss",
         "description": "Enfermedad y maternidad, cuota fija",
         "base": Decimal("3519.30"), "rate": Decimal("0.204"),
         "amount": Decimal("717.94"), "position": 0},
        {"component": "ceav", "group_key": "sar",
         "description": "Cesantía en edad avanzada y vejez",
         "base": Decimal("9917.40"), "rate": Decimal("0.06026"),
         "amount": Decimal("597.62"), "position": 8},
    ],
}


def test_saving_a_receipt_replaces_its_employer_cost(cursor):
    cursor.fetchone.return_value = {"id": 9, "created": False}

    PayrollRepository().save_payroll_receipt(_receipt(EMPLOYER_COST))

    queries = _queries(cursor)
    delete = queries.index(next(
        q for q in queries if q.startswith("DELETE FROM payroll_employer_costs")
    ))
    header = queries.index(next(
        q for q in queries if q.startswith("INSERT INTO payroll_employer_costs ")
    ))
    assert delete < header
    header_params = cursor.execute.call_args_list[header][0][1]
    assert header_params[0] == 9
    assert header_params[-1] == ["isn"]
    items = [
        call[0][1] for call in cursor.execute.call_args_list
        if "payroll_employer_cost_items" in call[0][0]
    ]
    assert [item[1] for item in items] == ["em_cuota_fija", "ceav"]


def test_saving_without_employer_cost_only_clears_the_old_one(cursor):
    cursor.fetchone.return_value = {"id": 9, "created": False}

    PayrollRepository().save_payroll_receipt(_receipt())

    queries = _queries(cursor)
    assert any(q.startswith("DELETE FROM payroll_employer_costs") for q in queries)
    assert not any("INSERT INTO payroll_employer_cost" in q for q in queries)


def test_employer_cost_parameters_read_what_is_in_force(cursor):
    cursor.fetchall.side_effect = [
        [{"key": "uma_diaria", "value": Decimal("117.31")}],
        [{"minimum_wage": True, "upper_uma": None, "rate": Decimal("0.0315")}],
    ]
    cursor.fetchone.side_effect = [{"rate": Decimal("0.03")}, None]

    params = PayrollRepository().employer_cost_parameters(
        COMPANY, date(2026, 9, 1)
    )

    assert params["rates"] == {"uma_diaria": Decimal("117.31")}
    assert params["ceav_brackets"][0]["minimum_wage"] is True
    assert params["isn_rate"] == Decimal("0.03")
    assert params["risk_rate"] is None
    isn_query, isn_params = cursor.execute.call_args_list[2][0]
    assert "entidad_federativa" in isn_query
    assert isn_params == (COMPANY, date(2026, 9, 1), date(2026, 9, 1))


# --- Prima de riesgo de trabajo -----------------------------------------------

@pytest.fixture
def owner_repository():
    with patch(OWNER_ROUTES) as repository:
        repository.get_owner_company.return_value = {
            "id": COMPANY, "legal_name": "Grupo Norte", "is_active": True,
            "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "risk_premium": {"rate": "0.0054355", "valid_from": "2026-03-01"},
        }
        yield repository


def test_owner_records_the_risk_premium(owner_repository):
    response = client.put(
        f"/owner/companies/{COMPANY}/risk-premium",
        json={"rate_percent": "0.54355", "valid_from": "2026-03-01"},
        headers=_headers("owner", 20),
    )

    assert response.status_code == 200
    owner_repository.set_risk_premium.assert_called_once_with(
        COMPANY, Decimal("0.0054355"), date(2026, 3, 1), 20
    )
    assert response.json()["risk_premium"]["valid_from"] == "2026-03-01"


@pytest.mark.parametrize("rate", ["0.4", "15.5"])
def test_risk_premium_outside_the_legal_range(owner_repository, rate):
    response = client.put(
        f"/owner/companies/{COMPANY}/risk-premium",
        json={"rate_percent": rate, "valid_from": "2026-03-01"},
        headers=_headers("owner", 20),
    )

    assert response.status_code == 422
    owner_repository.set_risk_premium.assert_not_called()


def test_risk_premium_of_a_foreign_company(owner_repository):
    response = client.put(
        "/owner/companies/2/risk-premium",
        json={"rate_percent": "1", "valid_from": "2026-03-01"},
        headers=_headers("owner", 20),
    )

    assert response.status_code == 404
    owner_repository.set_risk_premium.assert_not_called()


class _Overlap(psycopg2_errors.ExclusionViolation):
    @property
    def diag(self):
        return type(
            "Diag", (), {"constraint_name": "company_risk_premiums_no_overlap"}
        )()


def test_overlapping_risk_premium(owner_repository):
    owner_repository.set_risk_premium.side_effect = _Overlap()

    response = client.put(
        f"/owner/companies/{COMPANY}/risk-premium",
        json={"rate_percent": "1", "valid_from": "2026-03-01"},
        headers=_headers("owner", 20),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Ya hay una prima de riesgo registrada desde esa fecha"
    )


def test_new_risk_premium_closes_the_open_one(cursor):
    CompanyRepository().set_risk_premium(
        COMPANY, Decimal("0.0054355"), date(2026, 3, 1), 20
    )

    close, insert, audit = cursor.execute.call_args_list
    assert "valid_to = %s::date - 1" in close[0][0]
    assert close[0][1] == (date(2026, 3, 1), COMPANY, date(2026, 3, 1))
    assert insert[0][1] == (COMPANY, date(2026, 3, 1), Decimal("0.0054355"), 20)
    assert audit[0][1][1] == "company.risk_premium"


def test_risk_premium_keeps_at_most_five_decimals(owner_repository):
    response = client.put(
        f"/owner/companies/{COMPANY}/risk-premium",
        json={"rate_percent": "0.543551", "valid_from": "2026-03-01"},
        headers=_headers("owner", 20),
    )

    assert response.status_code == 422
