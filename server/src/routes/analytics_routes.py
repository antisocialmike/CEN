from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..controllers.payroll_analytics import (
    MAX_RANGE_DAYS,
    build_analytics,
    default_period,
    empty_raw_analytics,
    previous_period,
)
from ..middlewares.auth_middleware import require_role
from ..middlewares.company_context import ensure_owner_company
from ..models.analytics_model import PayrollAnalytics
from ..models.payroll_model import Periodicity
from ..repositories.analytics_repository import analytics_repository

router = APIRouter(prefix="/owner", tags=["Owner analytics"])

ALL_COMPANIES = "all"


def _invalid(detail: str) -> HTTPException:
    return HTTPException(
        status_code=422, detail=detail
    )


def _parse_company(raw: str) -> Optional[int]:
    if raw == ALL_COMPANIES:
        return None
    try:
        return int(raw)
    except ValueError:
        raise _invalid("company_id debe ser el id de una empresa o 'all'")


@router.get("/analytics", response_model=PayrollAnalytics)
def payroll_analytics(
    company_id: str = Query(default=ALL_COMPANIES),
    start: Optional[date] = Query(default=None, alias="from"),
    end: Optional[date] = Query(default=None, alias="to"),
    periodicity: Optional[Periodicity] = Query(default=None),
    user: dict = Depends(require_role("owner")),
):
    selected = _parse_company(company_id)

    default_start, default_end = default_period(date.today())
    start = start or default_start
    end = end or default_end
    if start > end:
        raise _invalid("La fecha inicial es posterior a la final")
    if (end - start).days > MAX_RANGE_DAYS:
        raise _invalid("El rango no puede pasar de cinco años")
    previous_start, previous_end = previous_period(start, end)

    if selected is None:
        company_ids = analytics_repository.owner_company_ids(
            user["employee_id"]
        )
    else:
        company_ids = [ensure_owner_company(user, selected)]

    period = {
        "start": start, "end": end,
        "previous_start": previous_start, "previous_end": previous_end,
        "periodicity": periodicity,
    }
    if not company_ids:
        return build_analytics(empty_raw_analytics(), selected, period)

    raw = analytics_repository.payroll_analytics(
        company_ids, start, end, previous_start, previous_end,
        periodicity, compare_companies=selected is None,
    )
    return build_analytics(raw, selected, period)
