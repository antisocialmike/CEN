from fastapi import APIRouter, HTTPException
from server.src.models.auth_model import LoginRequest, TokenResponse
from server.src.middlewares.auth_middleware import create_access_token, verify_password
from server.src.repositories.payroll_repository import PayrollRepository

router = APIRouter(prefix="/auth", tags=["Auth"])
payroll_repository = PayrollRepository()


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    employee = payroll_repository.get_employee_by_email(request.email)
    if employee is None or not verify_password(
        request.password, employee["password_hash"]
    ):
        raise HTTPException(status_code=401, detail="Credenciales invalidas")

    token = create_access_token(
        data={
            "sub": employee["email"],
            "role": employee["role"],
            "employee_id": employee["id"]
        }
    )
    return TokenResponse(access_token=token, role=employee["role"])
