from typing import List

from fastapi import APIRouter, Depends

from ..middlewares.auth_middleware import require_role
from ..models.platform_model import AdminCompany
from ..repositories.company_repository import company_repository

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/companies", response_model=List[AdminCompany])
def list_my_companies(user: dict = Depends(require_role("admin"))):
    """Las empresas activas que administra: el cliente elige entre ellas."""
    return company_repository.list_admin_companies(user["employee_id"])
