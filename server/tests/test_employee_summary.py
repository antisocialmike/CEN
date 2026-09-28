from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from server.src.controllers.payroll_analytics import build_employee_summary
from server.src.main import app
from server.src.middlewares.auth_middleware import create_access_token
from server.src.models.payroll_model import next_period_start
from server.src.repositories.analytics_repository import (
    EMPLOYEE_RECENT_PERIODS,
    AnalyticsRepository,
)

client = TestClient(app)

EMPLOYEE_ID = 7
REPOSITORY = "server.src.routes.payroll_routes.analytics_repository"


def _headers(employee_id=EMPLOYEE_ID) -> dict:
    data = {"sub": "empleado@cen.com", "role": "employee"}
    if employee_id is not None:
        data["employee_id"] = employee_id
    return {"Authorization": f"Bearer {create_access_token(data=data)}"}


def _receipt(receipt_id, start, end, periodicity="quincenal", net="7500.00"):
    return {
        "id": receipt_id, "period_start": start, "period_end": end,
        "periodicity": periodicity, "net_salary": Decimal(net),
        "total_perceptions": Decimal("9000.00"),
    }


def _year(receipts=2):
    return {
        "gross_payroll": Decimal("18000.00"), "isr_withheld": Decimal("1900.00"),
        "imss_withheld": Decimal("600.00"), "net_paid": Decimal("15500.00"),
        "receipts": receipts,
    }


# --- El siguiente periodo ----------------------------------------------------

@pytest.mark.parametrize("periodicity, start, expected", [
    ("mensual", date(2026, 9, 1), date(2026, 10, 1)),
    ("mensual", date(2026, 12, 1), date(2027, 1, 1)),
    ("quincenal", date(2026, 9, 1), date(2026, 9, 16)),
    ("quincenal", date(2026, 9, 16), date(2026, 10, 1)),
    ("quincenal", date(2026, 12, 16), date(2027, 1, 1)),
    ("semanal", date(2026, 9, 22), date(2026, 9, 29)),
    # La ultima semana de septiembre empieza el 29; la que sigue, el 1 de
    # octubre, como en la calculadora del admin.
    ("semanal", date(2026, 9, 29), date(2026, 10, 1)),
    ("semanal", date(2026, 2, 22), date(2026, 3, 1)),
])
def test_next_period_follows_the_calculator_cuts(periodicity, start, expected):
    assert next_period_start(periodicity, start) == expected


# --- El resumen --------------------------------------------------------------

def test_the_summary_estimates_the_next_period_from_the_latest_receipt():
    raw = {
        "year_totals": _year(),
        "recent": [
            _receipt(12, date(2026, 9, 1), date(2026, 9, 15)),
            _receipt(11, date(2026, 8, 16), date(2026, 8, 31)),
        ],
    }

    summary = build_employee_summary(raw, 2026)

    assert summary["latest"]["id"] == 12
    assert summary["next_period"] == {
        "periodicity": "quincenal",
        "start": date(2026, 9, 16), "end": date(2026, 9, 30),
    }
    assert summary["year_to_date"]["year"] == 2026
    assert summary["year_to_date"]["isr_withheld"] == Decimal("1900.00")
    # La grafica va del periodo mas viejo al mas nuevo.
    assert [item["id"] for item in summary["recent"]] == [11, 12]


def test_without_receipts_there_is_nothing_to_estimate():
    raw = {"year_totals": _year(receipts=0), "recent": []}

    summary = build_employee_summary(raw, 2026)

    assert summary["latest"] is None
    assert summary["next_period"] is None
    assert summary["recent"] == []
    assert summary["year_to_date"]["receipts"] == 0


# --- La ruta -----------------------------------------------------------------

@pytest.fixture
def repository():
    with patch(REPOSITORY) as mock:
        mock.employee_summary.return_value = {
            "year_totals": _year(),
            "recent": [_receipt(12, date(2026, 9, 1), date(2026, 9, 15))],
        }
        yield mock


def test_the_summary_is_the_one_of_the_token(repository):
    year = date.today().year

    response = client.get("/payroll/my-summary", headers=_headers())

    assert response.status_code == 200
    repository.employee_summary.assert_called_once_with(
        EMPLOYEE_ID, date(year, 1, 1), date(year + 1, 1, 1)
    )
    body = response.json()
    assert body["latest"]["id"] == 12
    assert body["latest"]["net_salary"] == 7500.0
    assert body["next_period"] == {
        "periodicity": "quincenal", "start": "2026-09-16", "end": "2026-09-30",
    }
    assert body["year_to_date"]["year"] == year


def test_a_token_without_employee_has_no_summary(repository):
    response = client.get("/payroll/my-summary", headers=_headers(None))

    assert response.status_code == 403
    repository.employee_summary.assert_not_called()


def test_the_summary_requires_a_session(repository):
    response = client.get("/payroll/my-summary")

    assert response.status_code == 401


# --- El repositorio ----------------------------------------------------------

@pytest.fixture
def cursor():
    with patch(
        "server.src.repositories.analytics_repository.db_cursor"
    ) as mock_db_cursor:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = _year()
        mock_cursor.fetchall.return_value = [
            _receipt(12, date(2026, 9, 1), date(2026, 9, 15)),
        ]
        mock_db_cursor.return_value.__enter__.return_value = mock_cursor
        yield mock_cursor


def test_the_summary_reads_only_the_receipts_of_the_person(cursor):
    raw = AnalyticsRepository().employee_summary(
        EMPLOYEE_ID, date(2026, 1, 1), date(2027, 1, 1)
    )

    (snapshot,), (totals, totals_params), (recent, recent_params) = [
        call[0] for call in cursor.execute.call_args_list
    ]
    assert snapshot.startswith("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
    assert "r.employee_id = %s" in totals and "r.employee_id = %s" in recent
    assert totals_params == (EMPLOYEE_ID, date(2026, 1, 1), date(2027, 1, 1))
    assert recent_params == (EMPLOYEE_ID, EMPLOYEE_RECENT_PERIODS)
    assert "r.id DESC LIMIT %s" in recent
    assert raw["year_totals"]["receipts"] == 2
    assert [item["id"] for item in raw["recent"]] == [12]
