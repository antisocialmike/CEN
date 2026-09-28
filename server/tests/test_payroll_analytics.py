from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from server.src.controllers.payroll_analytics import (
    build_analytics,
    default_period,
    empty_raw_analytics,
    previous_period,
)
from server.src.main import app
from server.src.middlewares.auth_middleware import create_access_token
from server.src.repositories.analytics_repository import AnalyticsRepository

client = TestClient(app)

OWNER_ID = 20
MINE = 1
PARTNER = 3
FOREIGN = 2
REPOSITORY = "server.src.routes.analytics_routes.analytics_repository"
CONTEXT = "server.src.middlewares.company_context.company_repository"


def _headers(role: str = "owner") -> dict:
    token = create_access_token(data={
        "sub": role + "@cen.com", "role": role, "employee_id": OWNER_ID,
    })
    return {"Authorization": f"Bearer {token}"}


def _totals(gross, net, isr, imss, receipts, paid):
    return {
        "gross_payroll": Decimal(gross), "net_paid": Decimal(net),
        "isr_withheld": Decimal(isr), "imss_withheld": Decimal(imss),
        "total_deductions": Decimal(isr) + Decimal(imss),
        "receipts": receipts, "paid_employees": paid,
    }


def _employer(cost, covered, with_cost=2, incomplete=0, without=0):
    return {
        "employer_cost": Decimal(cost), "covered_gross": Decimal(covered),
        "receipts_with_cost": with_cost, "receipts_incomplete": incomplete,
        "receipts_without_cost": without,
    }


def _raw(**overrides):
    # Dos personas cobran en el periodo: 18,000.50 y 11,999.50 brutos.
    # El periodo anterior: 12,000 y 12,000. Cifras hechas a mano.
    raw = {
        "totals": _totals("30000.00", "25500.00", "3600.00", "900.00", 2, 2),
        "previous_totals": _totals(
            "24000.00", "20800.00", "2400.00", "800.00", 2, 2
        ),
        "monthly": [{
            "month": date(2026, 9, 1), "gross_payroll": Decimal("30000.00"),
            "net_paid": Decimal("25500.00"), "isr_withheld": Decimal("3600"),
            "imss_withheld": Decimal("900"),
            "total_deductions": Decimal("4500"), "receipts": 2,
        }],
        "concepts": [{
            "kind": "perception", "concept": "sueldo",
            "description": "Sueldo del periodo", "amount": Decimal("30000"),
            "taxable": Decimal("30000"), "exempt": Decimal("0"),
        }],
        "headcount": {"active": 3, "inactive": 1},
        "headcount_by_month": [
            {"month": date(2026, 9, 1), "hires": 1, "terminations": 0},
        ],
        "top_salaries": [{
            "id": 1, "name": "Ana", "company_name": "Grupo Norte",
            "base_salary": Decimal("18000.50"),
        }],
        "salary_histogram": [{
            "label": "10,000 a 20,000", "min_salary": 10000,
            "max_salary": 20000, "employees": 2,
        }],
        "companies": [],
        # Costo patronal: 6,000 sobre 30,000 de nomina; antes 4,800 sobre 24,000.
        "employer": _employer("6000.00", "30000.00", incomplete=1),
        "previous_employer": _employer("4800.00", "24000.00"),
        "employer_components": [{
            "group_key": "sar", "component": "ceav",
            "description": "Cesantía en edad avanzada y vejez",
            "amount": Decimal("2000.00"),
        }],
        "employer_missing": [{"name": "isn", "receipts": 1}],
        "employer_monthly": [{
            "month": date(2026, 9, 1), "imss": Decimal("3000.00"),
            "sar": Decimal("2000.00"), "infonavit": Decimal("1000.00"),
            "isn": Decimal("0"), "covered_gross": Decimal("30000.00"),
        }],
    }
    raw.update(overrides)
    return raw


PERIOD = {
    "start": date(2026, 9, 1), "end": date(2026, 9, 30),
    "previous_start": date(2026, 8, 2), "previous_end": date(2026, 8, 31),
    "periodicity": None,
}


# --- Periodos ----------------------------------------------------------------

@pytest.mark.parametrize("today, expected_start", [
    (date(2026, 9, 23), date(2025, 10, 1)),
    (date(2026, 1, 15), date(2025, 2, 1)),
    (date(2026, 12, 31), date(2026, 1, 1)),
])
def test_default_period_covers_twelve_months(today, expected_start):
    assert default_period(today) == (expected_start, today)


def test_previous_period_has_the_same_length():
    start, end = date(2026, 9, 1), date(2026, 9, 30)

    previous_start, previous_end = previous_period(start, end)

    assert previous_end == date(2026, 8, 31)
    assert previous_start == date(2026, 8, 2)
    assert previous_end - previous_start == end - start


# --- Indicadores ---------------------------------------------------------------

def test_kpis_and_their_change():
    result = build_analytics(_raw(), MINE, PERIOD)

    kpis = result["kpis"]
    assert kpis["gross_payroll"] == Decimal("30000.00")
    assert kpis["active_employees"] == 3
    # 30,000 / 2 personas pagadas; antes 24,000 / 2.
    assert kpis["average_cost_per_employee"] == Decimal("15000.00")
    change = kpis["change"]
    assert change["gross_payroll"] == Decimal("25.0")
    assert change["net_paid"] == Decimal("22.6")
    assert change["isr_withheld"] == Decimal("50.0")
    assert change["imss_withheld"] == Decimal("12.5")
    assert change["paid_employees"] == Decimal("0.0")
    assert change["average_cost_per_employee"] == Decimal("25.0")


def test_total_cost_adds_the_employer_cost():
    kpis = build_analytics(_raw(), MINE, PERIOD)["kpis"]

    # 30,000 de nomina + 6,000 patronal; antes 24,000 + 4,800 = 28,800.
    assert kpis["employer_cost"] == Decimal("6000.00")
    assert kpis["total_cost"] == Decimal("36000.00")
    assert kpis["employer_cost_pct"] == Decimal("20.0")
    assert kpis["change"]["employer_cost"] == Decimal("25.0")
    assert kpis["change"]["total_cost"] == Decimal("25.0")


def test_employer_cost_percent_only_counts_covered_receipts():
    # 3,000 de costo sobre 20,000 de recibos con costo: 15%, aunque la
    # nomina completa sea de 30,000.
    raw = _raw(employer=_employer("3000.00", "20000.00", without=1))

    result = build_analytics(raw, MINE, PERIOD)

    assert result["kpis"]["employer_cost_pct"] == Decimal("15.0")
    assert result["employer_cost"]["coverage"]["receipts_without_cost"] == 1


def test_no_employer_cost_percent_without_covered_receipts():
    raw = _raw(employer=_employer("0", "0", with_cost=0, without=2))

    assert build_analytics(raw, MINE, PERIOD)["kpis"]["employer_cost_pct"] is None


def test_average_rounds_to_cents():
    raw = _raw(totals=_totals("10000.00", "0", "0", "0", 3, 3))

    kpis = build_analytics(raw, MINE, PERIOD)["kpis"]

    assert kpis["average_cost_per_employee"] == Decimal("3333.33")


def test_no_change_without_a_previous_period():
    raw = _raw(
        previous_totals=_totals("0", "0", "0", "0", 0, 0),
        previous_employer=_employer("0", "0", with_cost=0),
    )

    change = build_analytics(raw, MINE, PERIOD)["kpis"]["change"]

    assert all(value is None for value in change.values())


def test_no_average_when_nobody_was_paid():
    raw = empty_raw_analytics()

    kpis = build_analytics(raw, None, PERIOD)["kpis"]

    assert kpis["average_cost_per_employee"] is None
    assert kpis["gross_payroll"] == 0


# --- La ruta -----------------------------------------------------------------

@pytest.fixture(autouse=True)
def owns_companies_1_and_3():
    with patch(CONTEXT) as context:
        context.owner_has_company.side_effect = (
            lambda owner_id, company_id: company_id in (MINE, PARTNER)
        )
        yield context


@pytest.fixture
def repository():
    with patch(REPOSITORY) as mock:
        mock.owner_company_ids.return_value = [MINE, PARTNER]
        mock.payroll_analytics.return_value = _raw()
        yield mock


@pytest.mark.parametrize("role", ["superadmin", "admin", "employee"])
def test_only_owners_see_analytics(role):
    assert client.get("/owner/analytics", headers=_headers(role)).status_code \
        == 403


def test_analytics_of_a_foreign_company_does_not_exist(repository):
    response = client.get(
        "/owner/analytics", params={"company_id": FOREIGN}, headers=_headers()
    )

    assert response.status_code == 404
    repository.payroll_analytics.assert_not_called()


def test_analytics_of_one_company(repository):
    response = client.get(
        "/owner/analytics",
        params={"company_id": MINE, "from": "2026-09-01", "to": "2026-09-30",
                "periodicity": "quincenal"},
        headers=_headers(),
    )

    assert response.status_code == 200
    args, kwargs = repository.payroll_analytics.call_args
    assert args == (
        [MINE], date(2026, 9, 1), date(2026, 9, 30),
        date(2026, 8, 2), date(2026, 8, 31), "quincenal",
    )
    assert kwargs == {"compare_companies": False}
    assert response.json()["company_id"] == MINE


def test_analytics_of_every_company_compares_them(repository):
    response = client.get("/owner/analytics", headers=_headers())

    assert response.status_code == 200
    repository.owner_company_ids.assert_called_once_with(OWNER_ID)
    args, kwargs = repository.payroll_analytics.call_args
    assert args[0] == [MINE, PARTNER]
    assert kwargs == {"compare_companies": True}
    body = response.json()
    assert body["company_id"] is None
    assert body["period"]["end"] == date.today().isoformat()


def test_amounts_travel_as_text(repository):
    body = client.get("/owner/analytics", headers=_headers()).json()

    assert body["kpis"]["gross_payroll"] == "30000.00"
    assert body["kpis"]["average_cost_per_employee"] == "15000.00"
    assert body["kpis"]["change"]["gross_payroll"] == "25.0"
    assert body["top_salaries"][0]["base_salary"] == "18000.50"
    assert body["monthly"][0]["month"] == "2026-09-01"
    assert body["kpis"]["total_cost"] == "36000.00"
    assert body["employer_cost"]["missing"] == [{"name": "isn", "receipts": 1}]
    assert body["employer_cost"]["monthly"][0]["sar"] == "2000.00"


def test_the_comparison_carries_the_cost_of_each_company(repository):
    repository.payroll_analytics.return_value = _raw(companies=[{
        "id": MINE, "legal_name": "Grupo Norte", "is_active": True,
        "gross_payroll": Decimal("25000.00"), "net_paid": Decimal("21000.00"),
        "employer_cost": Decimal("5000.00"),
        "total_cost": Decimal("30000.00"), "receipts": 1,
        "paid_employees": 1, "active_employees": 3,
    }])

    body = client.get("/owner/analytics", headers=_headers()).json()

    company = body["companies"][0]
    assert company["employer_cost"] == "5000.00"
    assert company["total_cost"] == "30000.00"


def test_an_owner_without_companies_gets_zeros(repository):
    repository.owner_company_ids.return_value = []

    response = client.get("/owner/analytics", headers=_headers())

    assert response.status_code == 200
    assert response.json()["kpis"]["gross_payroll"] == "0"
    repository.payroll_analytics.assert_not_called()


@pytest.mark.parametrize("params", [
    {"company_id": "todas"},
    {"from": "2026-09-30", "to": "2026-09-01"},
    {"from": "2020-01-01", "to": "2026-09-01"},
    {"periodicity": "anual"},
])
def test_rejects_invalid_filters(repository, params):
    response = client.get("/owner/analytics", params=params, headers=_headers())

    assert response.status_code == 422
    repository.payroll_analytics.assert_not_called()


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


def _run(compare: bool, periodicity=None):
    return AnalyticsRepository().payroll_analytics(
        [MINE, PARTNER], date(2026, 9, 1), date(2026, 9, 30),
        date(2026, 8, 2), date(2026, 8, 31), periodicity, compare,
    )


def test_every_query_reads_the_same_snapshot(cursor):
    _run(compare=True)

    first = cursor.execute.call_args_list[0][0][0]
    assert first.startswith("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")


def test_every_query_is_scoped_to_the_companies(cursor):
    _run(compare=True, periodicity="mensual")

    for call in cursor.execute.call_args_list[1:]:
        query, params = call[0]
        assert "ANY(%s)" in query
        assert [MINE, PARTNER] in params
        if "r.periodicity" in query:
            assert params.count("mensual") == 2


def test_the_previous_period_uses_its_own_dates(cursor):
    _run(compare=False)

    previous = cursor.execute.call_args_list[2][0][1]
    assert previous[1:3] == (date(2026, 8, 2), date(2026, 8, 31))


def test_employer_cost_queries_cover_both_periods(cursor):
    _run(compare=False)

    employer = [
        call[0][1] for call in cursor.execute.call_args_list
        if "payroll_employer_costs ec" in call[0][0]
        and "COUNT(ec.receipt_id)" in call[0][0]
    ]
    assert [params[1:3] for params in employer] == [
        (date(2026, 9, 1), date(2026, 9, 30)),
        (date(2026, 8, 2), date(2026, 8, 31)),
    ]


def test_the_comparison_adds_the_employer_cost_of_each_company(cursor):
    _run(compare=True)

    comparison = next(
        call[0][0] for call in cursor.execute.call_args_list
        if "FROM companies c" in call[0][0]
    )
    # Uno a uno con el recibo: el costo no duplica la nomina de la empresa.
    assert "LEFT JOIN payroll_employer_costs ec ON ec.receipt_id = r.id" in (
        comparison
    )
    assert "AS employer_cost" in comparison
    assert "AS total_cost" in comparison


def test_the_comparison_only_runs_for_every_company(cursor):
    result = _run(compare=False)

    queries = [call[0][0] for call in cursor.execute.call_args_list]
    assert not any("FROM companies c" in q for q in queries)
    assert result["companies"] == []
