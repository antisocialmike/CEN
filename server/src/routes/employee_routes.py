from typing import List

from fastapi import APIRouter, Depends

from ..middlewares.auth_middleware import hash_password, require_role
from ..models.payroll_model import Employee, EmployeeCreateRequest
from ..repositories.payroll_repository import payroll_repository

router = APIRouter(prefix="/employees", tags=["Employees"])


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
