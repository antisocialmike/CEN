from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from ..repositories.company_repository import company_repository
from .auth_middleware import require_role

COMPANY_HEADER = "X-Company-Id"

# 404 y no 403: quien no pertenece a una empresa no debe poder distinguir
# entre "no existe" y "no es tuya".
COMPANY_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Empresa no encontrada",
)
NO_COMPANY = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="No administras ninguna empresa activa",
)
COMPANY_REQUIRED = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Administras varias empresas: indica cual en la cabecera "
    + COMPANY_HEADER,
)


def resolve_admin_company(user: dict, company_id: Optional[int]) -> int:
    admin_id = user["employee_id"]
    if company_id is not None:
        if not company_repository.admin_has_company(admin_id, company_id):
            raise COMPANY_NOT_FOUND
        return company_id

    # Sin cabecera solo se adivina cuando no hay nada que elegir.
    companies = company_repository.admin_company_ids(admin_id)
    if not companies:
        raise NO_COMPANY
    if len(companies) > 1:
        raise COMPANY_REQUIRED
    return companies[0]


def require_admin_company(
    user: dict = Depends(require_role("admin")),
    company_id: Optional[int] = Header(default=None, alias=COMPANY_HEADER),
) -> dict:
    return {**user, "company_id": resolve_admin_company(user, company_id)}


def ensure_owner_company(user: dict, company_id: int) -> int:
    if not company_repository.owner_has_company(
        user["employee_id"], company_id
    ):
        raise COMPANY_NOT_FOUND
    return company_id
