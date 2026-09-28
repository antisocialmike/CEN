from typing import List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..middlewares.auth_middleware import (
    generate_temporary_password,
    hash_password,
)
from ..middlewares.company_context import require_admin_company
from ..models.payroll_model import (
    Employee,
    EmployeeCreateRequest,
    EmployeeUpdateRequest,
    PasswordResetResponse,
)
from ..models.pagination_model import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    Page,
    page_offset,
)
from ..repositories.payroll_repository import (
    SharedAdminError,
    payroll_repository,
)

router = APIRouter(prefix="/employees", tags=["Employees"])

EMPLOYEE_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Empleado no encontrado",
)
SHARED_ADMIN = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Esta persona tambien administra otras empresas, asi que su "
    "cuenta no se puede cambiar desde aqui",
)


@router.get("", response_model=Union[Page[Employee], List[Employee]])
def list_employees(
    page: Optional[int] = Query(default=None, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    user: dict = Depends(require_admin_company),
):
    # Sin `page` va la lista completa: el selector de la calculadora la necesita toda.
    if page is None:
        return payroll_repository.list_employees(user["company_id"])

    items, total = payroll_repository.page_employees(
        user["company_id"], page_size, page_offset(page, page_size)
    )
    return Page[Employee](items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=Employee)
def create_employee(
    request: EmployeeCreateRequest,
    user: dict = Depends(require_admin_company),
):
    employee_id = payroll_repository.create_employee({
        "name": request.name,
        "email": request.email,
        "role": request.role,
        "base_salary": request.base_salary,
        "tipo_regimen": request.tipo_regimen,
        "tipo_jornada": request.tipo_jornada,
        "password_hash": hash_password(request.password),
    }, user["company_id"], user.get("employee_id"))
    return Employee(
        id=employee_id,
        name=request.name,
        email=request.email,
        role=request.role,
        base_salary=request.base_salary,
        tipo_regimen=request.tipo_regimen,
        tipo_jornada=request.tipo_jornada,
    )


@router.put("/{employee_id}", response_model=Employee)
def update_employee(
    employee_id: int,
    request: EmployeeUpdateRequest,
    user: dict = Depends(require_admin_company),
):
    if employee_id == user.get("employee_id") and request.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes quitarte a ti mismo el rol de administrador",
        )

    try:
        employee = payroll_repository.update_employee(employee_id, {
            "name": request.name,
            "email": request.email,
            "role": request.role,
            "base_salary": request.base_salary,
            "tipo_regimen": request.tipo_regimen,
            "tipo_jornada": request.tipo_jornada,
        }, user["company_id"], user.get("employee_id"))
    except SharedAdminError:
        raise SHARED_ADMIN
    if employee is None:
        raise EMPLOYEE_NOT_FOUND

    return employee


@router.post("/{employee_id}/deactivate", response_model=Employee)
def deactivate_employee(
    employee_id: int,
    user: dict = Depends(require_admin_company),
):
    if employee_id == user.get("employee_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propia cuenta",
        )

    return _set_active(employee_id, False, user["company_id"])


def _set_active(employee_id: int, is_active: bool, company_id: int) -> dict:
    try:
        employee = payroll_repository.set_employee_active(
            employee_id, is_active, company_id
        )
    except SharedAdminError:
        raise SHARED_ADMIN
    if employee is None:
        raise EMPLOYEE_NOT_FOUND

    return employee


@router.post("/{employee_id}/activate", response_model=Employee)
def activate_employee(
    employee_id: int,
    user: dict = Depends(require_admin_company),
):
    return _set_active(employee_id, True, user["company_id"])


@router.post("/{employee_id}/reset-password", response_model=PasswordResetResponse)
def reset_employee_password(
    employee_id: int,
    user: dict = Depends(require_admin_company),
):
    if employee_id == user.get("employee_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tu propia contraseña se cambia desde tu cuenta",
        )

    temporary_password = generate_temporary_password()
    try:
        employee = payroll_repository.reset_password(
            employee_id, hash_password(temporary_password), user["company_id"]
        )
    except SharedAdminError:
        raise SHARED_ADMIN
    if employee is None:
        raise EMPLOYEE_NOT_FOUND

    return PasswordResetResponse(
        employee_id=employee["id"],
        name=employee["name"],
        email=employee["email"],
        temporary_password=temporary_password,
    )
