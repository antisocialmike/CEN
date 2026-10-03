from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from server.src.controllers.payroll_analytics import build_admin_summary
from server.src.main import app
from server.src.middlewares.auth_middleware import create_access_token
from server.src.repositories.analytics_repository import (
    ADMIN_MOVEMENTS_SHOWN,
    ADMIN_PENDING_SHOWN,
    AnalyticsRepository,
)

client = TestClient(app)

COMPANY = 1
REPOSITORY = "server.src.routes.admin_routes.analytics_repository"
CONTEXT = "server.src.middlewares.company_context.company_repository"
SEPTEMBER = date(2026, 9, 1)


def _headers(role: str = "admin") -> dict:
    token = create_access_token(data={
        "sub": role + "@cen.com", "role": role, "employee_id": 10,
    })
    return {"Authorization": f"Bearer {token}"}


def _last_month(month=date(2026, 8, 1), receipts=3):
    return {
        "month": month, "gross_payroll": Decimal("45000.00"),
        "net_paid": Decimal("39000.00"), "isr_withheld": Decimal("4700.00"),
        "imss_withheld": Decimal("1300.00"), "receipts": receipts,
        "paid_people": receipts,
    }


def _raw(**overrides):
    raw = {
        "pending": [
            {"id": 4, "name": "Javier Ontiveros", "tipo_regimen": "09",
             "total": 2},
            {"id": 6, "name": "Rodrigo Alcántara", "tipo_regimen": "02",
             "total": 2},
        ],
        "regimes": [{"tipo_regimen": "02", "people": 3}],
        "last_month": _last_month(),
        "movements": [{
            "id": 6, "name": "Rodrigo Alcántara", "kind": "alta",
            "happened_at": datetime(2026, 9, 10, 12, tzinfo=timezone.utc),
        }],
    }
    raw.update(overrides)
    return raw


# --- El resumen --------------------------------------------------------------

def test_the_summary_counts_who_is_missing_this_month():
    summary = build_admin_summary(_raw(), SEPTEMBER)

    assert summary["month"] == SEPTEMBER
    assert summary["on_payroll"] == 3
    assert summary["pending"] == {
        "total": 2,
        "people": [
            {"id": 4, "name": "Javier Ontiveros", "tipo_regimen": "09"},
            {"id": 6, "name": "Rodrigo Alcántara", "tipo_regimen": "02"},
        ],
    }
    assert summary["last_month"]["net_paid"] == Decimal("39000.00")
    assert summary["movements"][0]["kind"] == "alta"


def test_both_payroll_types_always_come_even_in_zero():
    summary = build_admin_summary(
        _raw(regimes=[{"tipo_regimen": "09", "people": 1}]), SEPTEMBER
    )

    assert summary["regimes"] == [
        {"tipo_regimen": "02", "people": 0},
        {"tipo_regimen": "09", "people": 1},
    ]
    assert summary["on_payroll"] == 1


def test_a_company_without_receipts_has_no_last_month():
    # Sin recibos, MAX(period_start) es NULL y la consulta devuelve una fila
    # con el mes vacio.
    raw = _raw(
        pending=[], regimes=[], movements=[],
        last_month={**_last_month(month=None, receipts=0)},
    )

    summary = build_admin_summary(raw, SEPTEMBER)

    assert summary["last_month"] is None
    assert summary["pending"] == {"total": 0, "people": []}
    assert summary["on_payroll"] == 0


# --- La ruta -----------------------------------------------------------------

@pytest.fixture
def repository():
    with patch(REPOSITORY) as mock:
        mock.admin_summary.return_value = _raw()
        yield mock


@pytest.fixture(autouse=True)
def admin_company():
    with patch(CONTEXT) as context:
        context.admin_company_ids.return_value = [COMPANY]
        context.admin_has_company.return_value = True
        yield context


def test_the_summary_is_the_one_of_the_active_company(repository):
    today = date.today()
    month = today.replace(day=1)
    next_month = date(today.year + (today.month == 12), today.month % 12 + 1, 1)

    response = client.get("/admin/summary", headers=_headers())

    assert response.status_code == 200
    repository.admin_summary.assert_called_once_with(COMPANY, month, next_month)
    body = response.json()
    assert body["month"] == month.isoformat()
    assert body["pending"]["total"] == 2
    assert body["last_month"]["gross_payroll"] == 45000.0
    assert body["regimes"][0] == {"tipo_regimen": "02", "people": 3}


@pytest.mark.parametrize("role", ["owner", "superadmin", "employee"])
def test_only_admins_see_the_company_summary(repository, role):
    response = client.get("/admin/summary", headers=_headers(role))

    assert response.status_code == 403
    repository.admin_summary.assert_not_called()


def test_the_summary_requires_a_session(repository):
    response = client.get("/admin/summary")

    assert response.status_code == 401


# --- El repositorio ----------------------------------------------------------

@pytest.fixture
def cursor():
    with patch(
        "server.src.repositories.analytics_repository.db_cursor"
    ) as mock_db_cursor:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = _last_month()
        mock_cursor.fetchall.return_value = []
        mock_db_cursor.return_value.__enter__.return_value = mock_cursor
        yield mock_cursor


def _run():
    return AnalyticsRepository().admin_summary(
        COMPANY, SEPTEMBER, date(2026, 10, 1)
    )


def test_every_admin_query_reads_the_same_snapshot(cursor):
    _run()

    first = cursor.execute.call_args_list[0][0][0]
    assert first.startswith("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")


def test_every_admin_query_stays_in_the_company(cursor):
    _run()

    for query, params in (call[0] for call in cursor.execute.call_args_list[1:]):
        assert "company_id = %s" in query
        assert params[0] == COMPANY


def test_pending_are_the_people_on_payroll_without_a_receipt_this_month(cursor):
    _run()

    pending = next(
        call[0] for call in cursor.execute.call_args_list
        if "NOT EXISTS" in call[0][0]
    )
    query, params = pending
    assert "em.is_active AND e.is_active" in query
    assert "r.company_id = %s" in query
    assert params == (
        COMPANY, COMPANY, SEPTEMBER, date(2026, 10, 1), ADMIN_PENDING_SHOWN,
    )


def test_movements_are_the_latest_hires_and_terminations(cursor):
    _run()

    query, params = next(
        call[0] for call in cursor.execute.call_args_list
        if "UNION ALL" in call[0][0]
    )
    assert "'alta'" in query and "'baja'" in query
    assert "ORDER BY happened_at DESC" in query
    assert params[-1] == ADMIN_MOVEMENTS_SHOWN


def test_the_repository_returns_the_last_month_row(cursor):
    raw = _run()

    assert raw["last_month"]["receipts"] == 3
    assert raw["pending"] == [] and raw["movements"] == []
