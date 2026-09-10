from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ..middlewares.auth_middleware import (
    generate_temporary_password,
    hash_password,
    require_role,
)
from ..models.payroll_model import (
    Employee,
    EmployeeCreateRequest,
    EmployeeUpdateRequest,
    PasswordResetResponse,
)
from ..repositories.payroll_repository import payroll_repository

router = APIRouter(prefix="/employees", tags=["Employees"])

EMPLOYEE_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Empleado no encontrado",
)


@router.get("", response_model=List[Employee])
def list_employees(user: dict = Depends(require_role("admin"))):
    return payroll_repository.list_employees()


@router.post("", response_model=Employee)
def create_employee(
    request: EmployeeCreateRequest,
    user: dict = Depends(require_role("admin")),
):
    employee_id = payroll_repository.create_employee({
        "name": request.name,
        "email": request.email,
        "role": request.role,
        "base_salary": request.base_salary,
        "password_hash": hash_password(request.password),
    })
    return Employee(
        id=employee_id,
        name=request.name,
        email=request.email,
        role=request.role,
        base_salary=request.base_salary,
    )


@router.put("/{employee_id}", response_model=Employee)
def update_employee(
    employee_id: int,
    request: EmployeeUpdateRequest,
    user: dict = Depends(require_role("admin")),
):
    if employee_id == user.get("employee_id") and request.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes quitarte a ti mismo el rol de administrador",
        )

    employee = payroll_repository.update_employee(employee_id, {
        "name": request.name,
        "email": request.email,
        "role": request.role,
        "base_salary": request.base_salary,
    })
    if employee is None:
        raise EMPLOYEE_NOT_FOUND

    return employee


@router.post("/{employee_id}/deactivate", response_model=Employee)
def deactivate_employee(
    employee_id: int,
    user: dict = Depends(require_role("admin")),
):
    if employee_id == user.get("employee_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propia cuenta",
        )

    employee = payroll_repository.set_employee_active(employee_id, False)
    if employee is None:
        raise EMPLOYEE_NOT_FOUND

    return employee


@router.post("/{employee_id}/activate", response_model=Employee)
def activate_employee(
    employee_id: int,
    user: dict = Depends(require_role("admin")),
):
    employee = payroll_repository.set_employee_active(employee_id, True)
    if employee is None:
        raise EMPLOYEE_NOT_FOUND

    return employee


@router.post("/{employee_id}/reset-password", response_model=PasswordResetResponse)
def reset_employee_password(
    employee_id: int,
    user: dict = Depends(require_role("admin")),
):
    if employee_id == user.get("employee_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tu propia contraseña se cambia desde tu cuenta",
        )

    temporary_password = generate_temporary_password()
    employee = payroll_repository.reset_password(
        employee_id, hash_password(temporary_password)
    )
    if employee is None:
        raise EMPLOYEE_NOT_FOUND

    return PasswordResetResponse(
        employee_id=employee["id"],
        name=employee["name"],
        email=employee["email"],
        temporary_password=temporary_password,
    )
