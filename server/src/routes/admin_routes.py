from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends

from ..controllers.payroll_analytics import build_admin_summary
from ..middlewares.auth_middleware import require_role
from ..middlewares.company_context import require_admin_company
from ..models.platform_model import AdminCompany
from ..repositories.analytics_repository import analytics_repository
from ..repositories.company_repository import company_repository

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/companies", response_model=List[AdminCompany])
def list_my_companies(user: dict = Depends(require_role("admin"))):
    """Las empresas activas que administra: el cliente elige entre ellas."""
    return company_repository.list_admin_companies(user["employee_id"])


@router.get("/summary")
def admin_summary(user: dict = Depends(require_admin_company)):
    """El resumen de la empresa activa. La empresa sale de la cabecera ya
    validada contra las asignaciones del admin, nunca de un parametro."""
    month = date.today().replace(day=1)
    # Del dia 1 mas 31 dias siempre se cae en el mes siguiente.
    next_month = (month + timedelta(days=31)).replace(day=1)
    raw = analytics_repository.admin_summary(
        user["company_id"], month, next_month
    )
    return build_admin_summary(raw, month)
