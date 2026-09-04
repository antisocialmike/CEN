from fastapi import APIRouter, Depends, HTTPException
from psycopg2 import errors as psycopg2_errors
from server.src.models.payroll_model import Employee, EmployeeCreateRequest
from server.src.middlewares.auth_middleware import require_role, hash_password
from server.src.repositories.payroll_repository import PayrollRepository

router = APIRouter(prefix="/employees", tags=["Employees"])
payroll_repository = PayrollRepository()


@router.post("", response_model=Employee)
def create_employee(
    request: EmployeeCreateRequest,
    user: dict = Depends(require_role("admin"))
):
    try:
        employee_id = payroll_repository.create_employee({
            "name": request.name,
            "email": request.email,
            "role": request.role,
            "base_salary": request.base_salary,
            "password_hash": hash_password(request.password)
        })
    except psycopg2_errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="El correo ya esta registrado")

    return Employee(
        id=employee_id,
        name=request.name,
        email=request.email,
        role=request.role,
        base_salary=request.base_salary
    )
