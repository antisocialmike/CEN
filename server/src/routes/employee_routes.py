from datetime import date
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
    SalaryChange,
)
from ..models.pagination_model import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    Page,
    page_offset,
)
from ..repositories.payroll_repository import (
    AlreadyEmployedError,
    SharedAdminError,
    SharedPersonError,
    payroll_repository,
)

router = APIRouter(prefix="/employees", tags=["Employees"])

EMPLOYEE_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Empleado no encontrado",
)
SHARED_ADMIN = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Esta persona también administra otras empresas, así que su "
    "cuenta no se puede cambiar desde aquí",
)
SHARED_PERSON = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Esta persona también trabaja en otra empresa: aquí puedes cambiar "
    "su salario, tipo de nómina, jornada y fecha de ingreso, pero no su "
    "nombre, correo, rol ni datos fiscales",
)
SHARED_PASSWORD = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Esta persona también trabaja en otra empresa: puede recuperar su "
    "contraseña desde el inicio de sesión",
)
EMAIL_TAKEN = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="El correo ya está registrado",
)
CURP_TO_LINK = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Ese correo ya tiene cuenta en CEN. Para agregar a esa persona a tu "
    "empresa, captura su CURP tal como la tiene registrada",
)
ALREADY_HERE = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Esa persona ya está en tu empresa",
)
ALREADY_LEFT = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Esa persona ya estuvo en tu empresa: reactívala desde Usuarios",
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
    hire_date = request.hire_date or date.today()
    existing = payroll_repository.get_employee_by_email(request.email)
    if existing is not None:
        return _hire_existing(existing, request, hire_date, user)

    employee_id = payroll_repository.create_employee({
        "name": request.name,
        "email": request.email,
        "role": request.role,
        "base_salary": request.base_salary,
        "tipo_regimen": request.tipo_regimen,
        "tipo_jornada": request.tipo_jornada,
        "hire_date": hire_date,
        "rfc": request.rfc,
        "curp": request.curp,
        "nss": request.nss,
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
        hire_date=hire_date,
        rfc=request.rfc,
        curp=request.curp,
        nss=request.nss,
    )


def _hire_existing(
    existing: dict, request: EmployeeCreateRequest, hire_date: date, user: dict
) -> Employee:
    if existing["role"] != "employee" or request.role != "employee":
        raise EMAIL_TAKEN
    if request.curp is None or existing.get("curp") != request.curp:
        raise CURP_TO_LINK
    try:
        row = payroll_repository.hire_existing_employee(existing["id"], {
            "base_salary": request.base_salary,
            "tipo_regimen": request.tipo_regimen,
            "tipo_jornada": request.tipo_jornada,
            "hire_date": hire_date,
        }, user["company_id"], user.get("employee_id"))
    except AlreadyEmployedError as error:
        raise ALREADY_LEFT if not error.is_active else ALREADY_HERE
    return Employee(**row, linked=True)


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
            "hire_date": request.hire_date,
            "rfc": request.rfc,
            "curp": request.curp,
            "nss": request.nss,
            "salary_valid_from": request.salary_valid_from,
        }, user["company_id"], user.get("employee_id"))
    except SharedAdminError:
        raise SHARED_ADMIN
    except SharedPersonError:
        raise SHARED_PERSON
    if employee is None:
        raise EMPLOYEE_NOT_FOUND

    return employee


@router.get("/{employee_id}/salary-history", response_model=List[SalaryChange])
def get_salary_history(
    employee_id: int,
    user: dict = Depends(require_admin_company),
):
    history = payroll_repository.salary_history(employee_id, user["company_id"])
    if history is None:
        raise EMPLOYEE_NOT_FOUND
    return history


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
    except SharedPersonError:
        raise SHARED_PASSWORD
    if employee is None:
        raise EMPLOYEE_NOT_FOUND

    return PasswordResetResponse(
        employee_id=employee["id"],
        name=employee["name"],
        email=employee["email"],
        temporary_password=temporary_password,
    )
