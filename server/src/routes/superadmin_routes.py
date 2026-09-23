from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ..middlewares.auth_middleware import (
    generate_temporary_password,
    hash_password,
    require_role,
)
from ..models.platform_model import (
    Company,
    CompanyCreateRequest,
    CompanyOwnerAssignRequest,
    CompanyUpdateRequest,
    Owner,
    OwnerCreatedResponse,
    OwnerCreateRequest,
    OwnerPasswordResetResponse,
    OwnerUpdateRequest,
)
from ..repositories.company_repository import (
    NotFoundError,
    OrphanedCompanyError,
    company_repository,
)

router = APIRouter(prefix="/superadmin", tags=["Superadmin"])

require_superadmin = require_role("superadmin")

OWNER_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Dueno no encontrado",
)
COMPANY_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Empresa o dueno no encontrado",
)


def _orphaned(error: OrphanedCompanyError) -> HTTPException:
    names = ", ".join(company["legal_name"] for company in error.companies)
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Estas empresas se quedarían sin ningún dueño activo: "
        + names,
    )


def _owner_or_404(owner_id: int) -> dict:
    owner = company_repository.get_owner(owner_id)
    if owner is None:
        raise OWNER_NOT_FOUND
    return owner


def _company_or_404(company_id: int) -> dict:
    company = company_repository.get_company(company_id)
    if company is None:
        raise COMPANY_NOT_FOUND
    return company


@router.get("/owners", response_model=List[Owner])
def list_owners(user: dict = Depends(require_superadmin)):
    return company_repository.list_owners()


@router.post(
    "/owners",
    response_model=OwnerCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_owner(
    request: OwnerCreateRequest,
    user: dict = Depends(require_superadmin),
):
    temporary_password = generate_temporary_password()
    owner_id = company_repository.create_owner({
        "name": request.name,
        "email": request.email,
        "password_hash": hash_password(temporary_password),
    }, user["employee_id"])
    return OwnerCreatedResponse(
        owner=_owner_or_404(owner_id),
        temporary_password=temporary_password,
    )


@router.put("/owners/{owner_id}", response_model=Owner)
def update_owner(
    owner_id: int,
    request: OwnerUpdateRequest,
    user: dict = Depends(require_superadmin),
):
    try:
        company_repository.update_owner(owner_id, {
            "name": request.name,
            "email": request.email,
        }, user["employee_id"])
    except NotFoundError:
        raise OWNER_NOT_FOUND
    return _owner_or_404(owner_id)


@router.post("/owners/{owner_id}/deactivate", response_model=Owner)
def deactivate_owner(
    owner_id: int,
    user: dict = Depends(require_superadmin),
):
    try:
        company_repository.set_owner_active(
            owner_id, False, user["employee_id"]
        )
    except NotFoundError:
        raise OWNER_NOT_FOUND
    except OrphanedCompanyError as error:
        raise _orphaned(error)
    return _owner_or_404(owner_id)


@router.post("/owners/{owner_id}/activate", response_model=Owner)
def activate_owner(
    owner_id: int,
    user: dict = Depends(require_superadmin),
):
    try:
        company_repository.set_owner_active(
            owner_id, True, user["employee_id"]
        )
    except NotFoundError:
        raise OWNER_NOT_FOUND
    return _owner_or_404(owner_id)


@router.post(
    "/owners/{owner_id}/reset-password",
    response_model=OwnerPasswordResetResponse,
)
def reset_owner_password(
    owner_id: int,
    user: dict = Depends(require_superadmin),
):
    temporary_password = generate_temporary_password()
    try:
        owner = company_repository.reset_owner_password(
            owner_id, hash_password(temporary_password), user["employee_id"]
        )
    except NotFoundError:
        raise OWNER_NOT_FOUND
    return OwnerPasswordResetResponse(
        owner_id=owner["id"],
        name=owner["name"],
        email=owner["email"],
        temporary_password=temporary_password,
    )


@router.get("/companies", response_model=List[Company])
def list_companies(user: dict = Depends(require_superadmin)):
    return company_repository.list_companies()


@router.post(
    "/companies",
    response_model=Company,
    status_code=status.HTTP_201_CREATED,
)
def create_company(
    request: CompanyCreateRequest,
    user: dict = Depends(require_superadmin),
):
    try:
        company_id = company_repository.create_company(
            request.model_dump(exclude={"owner_id"}),
            request.owner_id,
            user["employee_id"],
        )
    except NotFoundError:
        raise OWNER_NOT_FOUND
    return _company_or_404(company_id)


@router.put("/companies/{company_id}", response_model=Company)
def update_company(
    company_id: int,
    request: CompanyUpdateRequest,
    user: dict = Depends(require_superadmin),
):
    try:
        company_repository.update_company(
            company_id, request.model_dump(), user["employee_id"]
        )
    except NotFoundError:
        raise COMPANY_NOT_FOUND
    return _company_or_404(company_id)


@router.post("/companies/{company_id}/owners", response_model=Company)
def assign_owner(
    company_id: int,
    request: CompanyOwnerAssignRequest,
    user: dict = Depends(require_superadmin),
):
    try:
        company_repository.assign_owner(
            company_id, request.owner_id, user["employee_id"]
        )
    except NotFoundError:
        raise COMPANY_NOT_FOUND
    return _company_or_404(company_id)


@router.delete(
    "/companies/{company_id}/owners/{owner_id}", response_model=Company
)
def unassign_owner(
    company_id: int,
    owner_id: int,
    user: dict = Depends(require_superadmin),
):
    try:
        company_repository.unassign_owner(
            company_id, owner_id, user["employee_id"]
        )
    except NotFoundError:
        raise COMPANY_NOT_FOUND
    except OrphanedCompanyError as error:
        raise _orphaned(error)
    return _company_or_404(company_id)
