from datetime import datetime, timezone
import secrets
import string

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Response,
    status,
)

from ..config.settings import (
    LOGIN_LOCK_MINUTES,
    LOGIN_MAX_ATTEMPTS,
    LOGIN_RATE_LIMIT,
    PASSWORD_RESET_COOLDOWN_SECONDS,
    PASSWORD_RESET_MAX_ATTEMPTS,
    PASSWORD_RESET_MAX_PER_HOUR,
    PASSWORD_RESET_REQUEST_RATE_LIMIT,
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
    PASSWORD_RESET_VERIFY_RATE_LIMIT,
)
from ..middlewares.auth_middleware import (
    create_access_token,
    get_user_changing_password,
    hash_password,
    hash_reset_code,
    reset_code_matches,
    verify_password,
)
from ..middlewares.rate_limit import rate_limit
from ..models.auth_model import (
    LoginRequest,
    PasswordChangeRequest,
    PasswordChangeResponse,
    PasswordResetRequest,
    PasswordResetVerify,
    TokenResponse,
)
from ..repositories.auth_repository import auth_repository
from ..repositories.payroll_repository import payroll_repository
from ..utils.email_service import send_password_reset_email

router = APIRouter(prefix="/auth", tags=["Auth"])

INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciales inválidas",
)
INVALID_RESET_CODE = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Código inválido o expirado",
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


def _issue_token(employee: dict) -> str:
    return create_access_token(data={
        "sub": employee["email"],
        "role": employee["role"],
        "employee_id": employee["id"],
        "name": employee.get("name", ""),
        "ver": employee.get("token_version", 0),
    })


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit("login", LOGIN_RATE_LIMIT))],
)
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
            detail="Esta cuenta está desactivada",
        )

    if employee.get("company_is_active") is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu empresa está desactivada",
        )

    payroll_repository.clear_failed_logins(employee["id"])

    return TokenResponse(
        access_token=_issue_token(employee),
        role=employee["role"],
        name=employee.get("name", ""),
        employee_id=employee["id"],
        must_change_password=bool(employee.get("must_change_password")),
    )


@router.post("/password", response_model=PasswordChangeResponse)
def change_password(
    request: PasswordChangeRequest,
    user: dict = Depends(get_user_changing_password),
):
    employee_id = user["employee_id"]
    current_hash = payroll_repository.get_password_hash(employee_id)
    if current_hash is None or not verify_password(
        request.current_password, current_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual no es correcta",
        )

    if request.new_password == request.current_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña nueva debe ser distinta de la actual",
        )

    payroll_repository.update_password(
        employee_id, hash_password(request.new_password)
    )

    employee = payroll_repository.get_employee_by_email(user["username"])
    if employee is None:
        raise INVALID_CREDENTIALS
    return PasswordChangeResponse(access_token=_issue_token(employee))


def _generate_reset_code() -> str:
    digits = string.digits
    return "".join(secrets.choice(digits) for _ in range(6))


def _can_recover(employee) -> bool:
    return (
        employee is not None
        and employee.get("is_active", True)
        and employee.get("company_is_active") is not False
    )


@router.post(
    "/password-reset/request",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit(
        "password-reset-request", PASSWORD_RESET_REQUEST_RATE_LIMIT
    ))],
)
def request_password_reset(
    request: PasswordResetRequest, background_tasks: BackgroundTasks
):
    employee = payroll_repository.get_employee_by_email(request.email)
    if not _can_recover(employee):
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    code = _generate_reset_code()
    issued = auth_repository.issue_reset_code(
        employee["id"],
        hash_reset_code(code),
        PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
        PASSWORD_RESET_COOLDOWN_SECONDS,
        PASSWORD_RESET_MAX_PER_HOUR,
    )
    if issued:
        background_tasks.add_task(
            send_password_reset_email,
            email=employee["email"],
            name=employee["name"],
            code=code,
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/password-reset/verify",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit(
        "password-reset-verify", PASSWORD_RESET_VERIFY_RATE_LIMIT
    ))],
)
def verify_password_reset(request: PasswordResetVerify):
    employee = payroll_repository.get_employee_by_email(request.email)
    if not _can_recover(employee):
        raise INVALID_RESET_CODE

    reset_code = auth_repository.claim_reset_attempt(
        employee["id"], PASSWORD_RESET_MAX_ATTEMPTS
    )
    if reset_code is None or not reset_code_matches(
        request.code, reset_code["code_hash"]
    ):
        raise INVALID_RESET_CODE

    if not auth_repository.reset_password_with_code(
        reset_code["id"], employee["id"], hash_password(request.new_password)
    ):
        raise INVALID_RESET_CODE

    return Response(status_code=status.HTTP_204_NO_CONTENT)
