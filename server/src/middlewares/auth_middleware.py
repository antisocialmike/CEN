import hashlib
import hmac
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from ..config.settings import (
    JWT_ALGORITHM,
    JWT_EXPIRATION_HOURS,
    JWT_SECRET_KEY,
    TEMPORARY_PASSWORD_LENGTH,
)
from ..repositories.auth_repository import auth_repository

security_bearer = HTTPBearer()
BCRYPT_MAX_BYTES = 72
AMBIGUOUS_CHARACTERS = "0O1lI"
TEMPORARY_PASSWORD_ALPHABET = "".join(
    character
    for character in string.ascii_letters + string.digits
    if character not in AMBIGUOUS_CHARACTERS
)

INVALID_TOKEN = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token no valido",
)
PASSWORD_CHANGE_REQUIRED = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Debes cambiar tu contrasena temporal antes de continuar",
)


def generate_temporary_password() -> str:
    return "".join(
        secrets.choice(TEMPORARY_PASSWORD_ALPHABET)
        for _ in range(TEMPORARY_PASSWORD_LENGTH)
    )


def _encode(password: str) -> bytes:
    return password.encode("utf-8")[:BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_encode(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(_encode(password), password_hash.encode("utf-8"))


def hash_reset_code(code: str) -> str:
    return hmac.new(
        JWT_SECRET_KEY.encode("utf-8"), code.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def reset_code_matches(code: str, code_hash: str) -> bool:
    return hmac.compare_digest(hash_reset_code(code), code_hash)


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    expires_in = expires_delta or timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": datetime.now(timezone.utc) + expires_in})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def _session_is_current(state: Optional[dict], token_version: int) -> bool:
    return (
        state is not None
        and bool(state["same_role"])
        and bool(state["is_active"])
        and state.get("company_is_active") is not False
        and state["token_version"] == token_version
    )


def _authenticate(credentials: HTTPAuthorizationCredentials) -> tuple:
    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
    except JWTError as error:
        raise INVALID_TOKEN from error

    username = str(payload.get("sub") or "")
    role = str(payload.get("role") or "")
    employee_id = payload.get("employee_id")
    if not username or not role or not isinstance(employee_id, int):
        raise INVALID_TOKEN

    state = auth_repository.session_state(employee_id, role)
    if not _session_is_current(state, payload.get("ver", 0)):
        raise INVALID_TOKEN

    user = {
        "username": username,
        "role": role,
        "employee_id": employee_id,
        "company_id": payload.get("company_id"),
    }
    return user, bool(state["must_change_password"])


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security_bearer)
) -> dict:
    user, must_change_password = _authenticate(credentials)
    if must_change_password:
        raise PASSWORD_CHANGE_REQUIRED
    return user


def get_user_changing_password(
    credentials: HTTPAuthorizationCredentials = Security(security_bearer)
) -> dict:
    user, _ = _authenticate(credentials)
    return user


def require_role(required_role: str):
    def role_checker(user: dict = Security(get_current_user)) -> dict:
        if user.get("role") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permisos insuficientes",
            )
        return user

    return role_checker
