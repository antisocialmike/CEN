from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from ..models.payroll_model import next_period_start, period_end_for

CENT = Decimal("0.01")
TENTH = Decimal("0.1")
DEFAULT_MONTHS = 12
MAX_RANGE_DAYS = 366 * 5

EMPTY_EMPLOYER = {
    "employer_cost": Decimal(0), "covered_gross": Decimal(0),
    "receipts_with_cost": 0, "receipts_incomplete": 0,
    "receipts_without_cost": 0,
}

CONCEPT_LABELS = {
    "sueldo": "Sueldos y salarios",
    "honorarios": "Honorarios asimilados a salarios",
    "horas_extra": "Horas extra",
    "aguinaldo": "Aguinaldo",
    "prima_vacacional": "Prima vacacional",
    "bono": "Bonos y gratificaciones",
    "isr": "ISR retenido",
    "imss": "IMSS retenido",
    "prestamo": "Préstamos a la empresa",
    "infonavit": "Crédito Infonavit",
}

EMPTY_TOTALS = {
    "gross_payroll": Decimal(0), "net_paid": Decimal(0),
    "isr_withheld": Decimal(0), "imss_withheld": Decimal(0),
    "total_deductions": Decimal(0), "receipts": 0, "paid_employees": 0,
}


def default_period(today: date) -> tuple:
    """Los ultimos doce meses completos mas el mes en curso."""
    month = today.month - (DEFAULT_MONTHS - 1)
    year = today.year
    while month < 1:
        month += 12
        year -= 1
    return date(year, month, 1), today


def previous_period(start: date, end: date) -> tuple:
    """El tramo de la misma duracion que termina justo antes de `start`."""
    length = end - start
    previous_end = start - timedelta(days=1)
    return previous_end - length, previous_end


def _average(total: Decimal, count: int) -> Optional[Decimal]:
    if not count:
        return None
    return (Decimal(total) / count).quantize(CENT, rounding=ROUND_HALF_UP)


def _change(current, previous) -> Optional[Decimal]:
    if current is None or previous is None or Decimal(previous) == 0:
        return None
    ratio = (Decimal(current) - Decimal(previous)) / Decimal(previous) * 100
    return ratio.quantize(TENTH, rounding=ROUND_HALF_UP)


def _percent_of(part, whole) -> Optional[Decimal]:
    if not whole:
        return None
    return (Decimal(part) / Decimal(whole) * 100).quantize(
        TENTH, rounding=ROUND_HALF_UP
    )


def build_analytics(
    raw: dict, company_id: Optional[int], period: dict
) -> dict:
    totals = raw["totals"]
    previous = raw["previous_totals"]
    employer = raw["employer"]
    previous_employer = raw["previous_employer"]
    total_cost = Decimal(totals["gross_payroll"]) + Decimal(
        employer["employer_cost"]
    )
    previous_total_cost = Decimal(previous["gross_payroll"]) + Decimal(
        previous_employer["employer_cost"]
    )
    average = _average(totals["gross_payroll"], totals["paid_employees"])
    previous_average = _average(
        previous["gross_payroll"], previous["paid_employees"]
    )
    changed = (
        "gross_payroll", "net_paid", "isr_withheld", "imss_withheld",
        "paid_employees",
    )

    return {
        "company_id": company_id,
        "period": period,
        "kpis": {
            **totals,
            "active_employees": raw["headcount"]["active"],
            "average_cost_per_employee": average,
            "employer_cost": employer["employer_cost"],
            "total_cost": total_cost,
            "employer_cost_pct": _percent_of(
                employer["employer_cost"], employer["covered_gross"]
            ),
            "change": {
                **{key: _change(totals[key], previous[key])
                   for key in changed},
                "average_cost_per_employee": _change(
                    average, previous_average
                ),
                "employer_cost": _change(
                    employer["employer_cost"],
                    previous_employer["employer_cost"],
                ),
                "total_cost": _change(total_cost, previous_total_cost),
            },
        },
        "monthly": raw["monthly"],
        "concepts": [
            {**concept, "description": CONCEPT_LABELS.get(
                concept["concept"], concept["description"]
            )}
            for concept in raw["concepts"]
        ],
        "headcount": {
            **raw["headcount"],
            "by_month": raw["headcount_by_month"],
        },
        "top_salaries": raw["top_salaries"],
        "salary_histogram": raw["salary_histogram"],
        "companies": raw["companies"],
        "employer_cost": {
            "coverage": {
                key: employer[key] for key in (
                    "receipts_with_cost", "receipts_incomplete",
                    "receipts_without_cost",
                )
            },
            "components": raw["employer_components"],
            "missing": raw["employer_missing"],
            "monthly": raw["employer_monthly"],
        },
    }


def empty_raw_analytics() -> dict:
    """Lo que devolveria la base para un dueno que aun no tiene empresas."""
    return {
        "totals": dict(EMPTY_TOTALS),
        "previous_totals": dict(EMPTY_TOTALS),
        "monthly": [],
        "concepts": [],
        "headcount": {"active": 0, "inactive": 0},
        "headcount_by_month": [],
        "top_salaries": [],
        "salary_histogram": [],
        "companies": [],
        "employer": dict(EMPTY_EMPLOYER),
        "previous_employer": dict(EMPTY_EMPLOYER),
        "employer_components": [],
        "employer_missing": [],
        "employer_monthly": [],
    }


def build_employee_summary(raw: dict, year: int) -> dict:
    """El resumen del empleado. `recent` llega del mas nuevo al mas viejo y
    sale al reves, en el orden en que se grafica.

    CEN no guarda fechas de pago: el siguiente periodo se estima con la
    periodicidad del ultimo recibo y la pantalla lo presenta como estimado."""
    recent = raw["recent"]
    latest = recent[0] if recent else None
    next_period = None
    if latest is not None:
        start = next_period_start(latest["periodicity"], latest["period_start"])
        next_period = {
            "periodicity": latest["periodicity"],
            "start": start,
            "end": period_end_for(latest["periodicity"], start),
        }
    return {
        "latest": latest,
        "next_period": next_period,
        "year_to_date": {"year": year, **raw["year_totals"]},
        "recent": list(reversed(recent)),
    }


def build_admin_summary(raw: dict, month: date) -> dict:
    """El resumen de la empresa activa para su admin.

    `pending` son quienes estan en la nomina y no tienen ningun recibo que
    empiece en `month`. Los dos tipos de nomina salen siempre, aunque sea en
    cero, para que la pantalla no tenga que adivinar cuales faltan."""
    pending = raw["pending"]
    regimes = {row["tipo_regimen"]: row["people"] for row in raw["regimes"]}
    last_month = raw["last_month"]
    if last_month is not None and last_month["month"] is None:
        last_month = None
    return {
        "month": month,
        "on_payroll": sum(regimes.values()),
        "pending": {
            "total": pending[0]["total"] if pending else 0,
            "people": [
                {key: row[key] for key in ("id", "name", "tipo_regimen")}
                for row in pending
            ],
        },
        "last_month": last_month,
        "movements": raw["movements"],
        "regimes": [
            {"tipo_regimen": key, "people": regimes.get(key, 0)}
            for key in ("02", "09")
        ],
    }


def build_platform_summary(raw: dict) -> dict:
    """El tablero del superadmin. Los tres roles salen siempre, aunque sea en
    cero, igual que los tipos de nomina del resumen del admin."""
    users = {row["role"]: row for row in raw["users"]}
    orphaned = raw["orphaned"]
    return {
        "companies": raw["companies"],
        "users": {
            role: {
                "active": users.get(role, {}).get("active", 0),
                "inactive": users.get(role, {}).get("inactive", 0),
            }
            for role in ("owner", "admin", "employee")
        },
        "orphaned": {
            "total": orphaned[0]["total"] if orphaned else 0,
            "companies": [
                {key: row[key] for key in ("id", "legal_name", "is_active")}
                for row in orphaned
            ],
        },
        "signups": raw["signups"],
        "activity": raw["activity"],
    }
