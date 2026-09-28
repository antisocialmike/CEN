from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from server.src.controllers.payroll_analytics import (
    build_platform_summary,
    default_period,
)
from server.src.main import app
from server.src.middlewares.auth_middleware import create_access_token
from server.src.repositories.analytics_repository import (
    PLATFORM_ACTIVITY_SHOWN,
    PLATFORM_ORPHANED_SHOWN,
    AnalyticsRepository,
)

client = TestClient(app)

REPOSITORY = "server.src.routes.superadmin_routes.analytics_repository"


def _headers(role: str = "superadmin") -> dict:
    token = create_access_token(data={
        "sub": role + "@cen.com", "role": role, "employee_id": 99,
    })
    return {"Authorization": f"Bearer {token}"}


def _raw(**overrides):
    raw = {
        "companies": {"active": 3, "inactive": 1},
        "users": [
            {"role": "admin", "active": 4, "inactive": 0},
            {"role": "employee", "active": 40, "inactive": 6},
            {"role": "owner", "active": 2, "inactive": 1},
        ],
        "orphaned": [
            {"id": 1, "legal_name": "Empresa principal", "is_active": True,
             "total": 1},
        ],
        "signups": [
            {"month": date(2026, 8, 1), "companies": 1, "owners": 0},
            {"month": date(2026, 9, 1), "companies": 2, "owners": 1},
        ],
        "activity": [{
            "id": 30, "action": "company.create", "target_type": "company",
            "created_at": datetime(2026, 9, 20, 17, tzinfo=timezone.utc),
            "actor_name": "Sofia Castaneda",
            "target_name": "Grupo Norte SA de CV",
        }],
    }
    raw.update(overrides)
    return raw


# --- El tablero --------------------------------------------------------------

def test_the_platform_summary_counts_by_role():
    summary = build_platform_summary(_raw())

    assert summary["companies"] == {"active": 3, "inactive": 1}
    assert summary["users"] == {
        "owner": {"active": 2, "inactive": 1},
        "admin": {"active": 4, "inactive": 0},
        "employee": {"active": 40, "inactive": 6},
    }
    assert summary["orphaned"] == {
        "total": 1,
        "companies": [
            {"id": 1, "legal_name": "Empresa principal", "is_active": True},
        ],
    }
    assert summary["activity"][0]["target_name"] == "Grupo Norte SA de CV"


def test_a_new_platform_has_every_role_in_zero():
    summary = build_platform_summary(_raw(
        companies={"active": 0, "inactive": 0}, users=[], orphaned=[],
        signups=[], activity=[],
    ))

    assert summary["users"]["admin"] == {"active": 0, "inactive": 0}
    assert summary["orphaned"] == {"total": 0, "companies": []}


# --- La ruta -----------------------------------------------------------------

@pytest.fixture
def repository():
    with patch(REPOSITORY) as mock:
        mock.platform_summary.return_value = _raw()
        yield mock


def test_the_summary_covers_the_last_twelve_months(repository):
    response = client.get("/superadmin/summary", headers=_headers())

    assert response.status_code == 200
    repository.platform_summary.assert_called_once_with(
        *default_period(date.today())
    )
    body = response.json()
    assert body["users"]["employee"]["active"] == 40
    assert body["signups"][1] == {
        "month": "2026-09-01", "companies": 2, "owners": 1,
    }


@pytest.mark.parametrize("role", ["owner", "admin", "employee"])
def test_only_the_superadmin_sees_the_platform(repository, role):
    response = client.get("/superadmin/summary", headers=_headers(role))

    assert response.status_code == 403
    repository.platform_summary.assert_not_called()


def test_the_platform_summary_requires_a_session(repository):
    response = client.get("/superadmin/summary")

    assert response.status_code == 401


# --- El repositorio ----------------------------------------------------------

@pytest.fixture
def cursor():
    with patch(
        "server.src.repositories.analytics_repository.db_cursor"
    ) as mock_db_cursor:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"active": 0, "inactive": 0}
        mock_cursor.fetchall.return_value = []
        mock_db_cursor.return_value.__enter__.return_value = mock_cursor
        yield mock_cursor


def _run():
    return AnalyticsRepository().platform_summary(
        date(2025, 10, 1), date(2026, 9, 26)
    )


def _queries(cursor):
    return [call[0] for call in cursor.execute.call_args_list]


def test_every_platform_query_reads_the_same_snapshot(cursor):
    _run()

    first = _queries(cursor)[0][0]
    assert first.startswith("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")


def test_the_platform_never_reads_payroll_amounts(cursor):
    _run()

    for query, *_ in _queries(cursor):
        assert "payroll_" not in query
        assert "salary" not in query


def test_orphaned_companies_are_the_ones_without_an_active_owner(cursor):
    _run()

    query, params = next(
        call for call in _queries(cursor) if "NOT EXISTS" in call[0]
    )
    assert "o.is_active" in query
    assert "COUNT(*) OVER ()" in query
    assert params == (PLATFORM_ORPHANED_SHOWN,)


def test_signups_go_month_by_month_within_the_period(cursor):
    _run()

    query, params = next(
        call for call in _queries(cursor) if "generate_series" in call[0]
    )
    assert "e.role = 'owner'" in query
    assert params == (date(2025, 10, 1), date(2026, 9, 26))


def test_the_activity_names_who_did_it_and_on_what(cursor):
    _run()

    query, params = next(
        call for call in _queries(cursor) if "platform_audit_log" in call[0]
    )
    assert "a.name AS actor_name" in query
    assert "COALESCE(o.name, c.legal_name) AS target_name" in query
    assert params == (PLATFORM_ACTIVITY_SHOWN,)
