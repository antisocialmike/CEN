from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ..middlewares.auth_middleware import (
    generate_temporary_password,
    hash_password,
    require_role,
)
from ..middlewares.company_context import (
    COMPANY_NOT_FOUND,
    ensure_owner_company,
)
from ..models.platform_model import (
    AdminAssignRequest,
    AdminInvitedResponse,
    AdminInviteRequest,
    CompanyUpdateRequest,
    OwnerCompany,
)
from ..repositories.company_repository import (
    NotFoundError,
    company_repository,
)

router = APIRouter(prefix="/owner", tags=["Owner"])

require_owner = require_role("owner")

ADMIN_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="No hay un administrador activo con ese correo",
)
ASSIGNMENT_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Esa persona no administra esta empresa",
)


def _owned_company(user: dict, company_id: int) -> dict:
    ensure_owner_company(user, company_id)
    company = company_repository.get_owner_company(
        user["employee_id"], company_id
    )
    if company is None:
        raise COMPANY_NOT_FOUND
    return company


@router.get("/companies", response_model=List[OwnerCompany])
def list_companies(user: dict = Depends(require_owner)):
    return company_repository.list_owner_companies(user["employee_id"])


@router.get("/companies/{company_id}", response_model=OwnerCompany)
def get_company(company_id: int, user: dict = Depends(require_owner)):
    return _owned_company(user, company_id)


@router.put("/companies/{company_id}", response_model=OwnerCompany)
def update_company(
    company_id: int,
    request: CompanyUpdateRequest,
    user: dict = Depends(require_owner),
):
    ensure_owner_company(user, company_id)
    company_repository.update_company(
        company_id, request.model_dump(), user["employee_id"]
    )
    return _owned_company(user, company_id)


@router.post("/companies/{company_id}/deactivate", response_model=OwnerCompany)
def deactivate_company(company_id: int, user: dict = Depends(require_owner)):
    return _set_active(user, company_id, False)


@router.post("/companies/{company_id}/activate", response_model=OwnerCompany)
def activate_company(company_id: int, user: dict = Depends(require_owner)):
    return _set_active(user, company_id, True)


def _set_active(user: dict, company_id: int, is_active: bool) -> dict:
    ensure_owner_company(user, company_id)
    company_repository.set_company_active(
        company_id, is_active, user["employee_id"]
    )
    return _owned_company(user, company_id)


@router.post(
    "/companies/{company_id}/admins/invite",
    response_model=AdminInvitedResponse,
    status_code=status.HTTP_201_CREATED,
)
def invite_admin(
    company_id: int,
    request: AdminInviteRequest,
    user: dict = Depends(require_owner),
):
    ensure_owner_company(user, company_id)
    temporary_password = generate_temporary_password()
    admin_id = company_repository.invite_admin(company_id, {
        "name": request.name,
        "email": request.email,
        "password_hash": hash_password(temporary_password),
    }, user["employee_id"])
    return AdminInvitedResponse(
        company=_owned_company(user, company_id),
        admin_id=admin_id,
        temporary_password=temporary_password,
    )


@router.post("/companies/{company_id}/admins", response_model=OwnerCompany)
def assign_admin(
    company_id: int,
    request: AdminAssignRequest,
    user: dict = Depends(require_owner),
):
    ensure_owner_company(user, company_id)
    try:
        company_repository.assign_admin_by_email(
            company_id, request.email, user["employee_id"]
        )
    except NotFoundError:
        raise ADMIN_NOT_FOUND
    return _owned_company(user, company_id)


@router.delete(
    "/companies/{company_id}/admins/{admin_id}",
    response_model=OwnerCompany,
)
def unassign_admin(
    company_id: int,
    admin_id: int,
    user: dict = Depends(require_owner),
):
    ensure_owner_company(user, company_id)
    try:
        company_repository.unassign_admin(
            company_id, admin_id, user["employee_id"]
        )
    except NotFoundError:
        raise ASSIGNMENT_NOT_FOUND
    return _owned_company(user, company_id)
