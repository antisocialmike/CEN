from fastapi import APIRouter, HTTPException, status

from ..middlewares.auth_middleware import create_access_token, verify_password
from ..models.auth_model import LoginRequest, TokenResponse
from ..repositories.payroll_repository import payroll_repository

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    employee = payroll_repository.get_employee_by_email(request.email)
    if employee is None or not verify_password(
        request.password, employee["password_hash"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas",
        )

    name = employee.get("name", "")
    token = create_access_token(data={
        "sub": employee["email"],
        "role": employee["role"],
        "employee_id": employee["id"],
        "name": name,
    })
    return TokenResponse(
        access_token=token,
        role=employee["role"],
        name=name,
        employee_id=employee["id"],
    )
