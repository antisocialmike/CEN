from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status

from ..config.settings import LOGIN_LOCK_MINUTES, LOGIN_MAX_ATTEMPTS
from ..middlewares.auth_middleware import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from ..models.auth_model import (
    LoginRequest,
    PasswordChangeRequest,
    TokenResponse,
)
from ..repositories.payroll_repository import payroll_repository

router = APIRouter(prefix="/auth", tags=["Auth"])

INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciales invalidas",
)


def _minutes_left(locked_until) -> int:
    remaining = locked_until - datetime.now(timezone.utc)
    return max(1, int(remaining.total_seconds() // 60) + 1)


def _too_many_attempts(locked_until) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Demasiados intentos fallidos. Vuelve a intentarlo en {} minutos".format(
            _minutes_left(locked_until)
        ),
    )


def _is_locked(locked_until) -> bool:
    return locked_until is not None and locked_until > datetime.now(timezone.utc)


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    employee = payroll_repository.get_employee_by_email(request.email)
    if employee is None:
        raise INVALID_CREDENTIALS

    if _is_locked(employee.get("locked_until")):
        raise _too_many_attempts(employee["locked_until"])

    if not verify_password(request.password, employee["password_hash"]):
        attempt = payroll_repository.register_failed_login(
            employee["id"], LOGIN_MAX_ATTEMPTS, LOGIN_LOCK_MINUTES
        )
        if attempt is not None and _is_locked(attempt.get("locked_until")):
            raise _too_many_attempts(attempt["locked_until"])
        raise INVALID_CREDENTIALS

    if not employee.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta cuenta esta desactivada",
        )

    payroll_repository.clear_failed_logins(employee["id"])

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
        must_change_password=bool(employee.get("must_change_password")),
    )


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    request: PasswordChangeRequest,
    user: dict = Depends(get_current_user),
):
    employee_id = user.get("employee_id")
    if employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token sin empleado asociado",
        )

    current_hash = payroll_repository.get_password_hash(employee_id)
    if current_hash is None or not verify_password(
        request.current_password, current_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contrasena actual no es correcta",
        )

    if request.new_password == request.current_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contrasena nueva debe ser distinta de la actual",
        )

    payroll_repository.update_password(
        employee_id, hash_password(request.new_password)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
