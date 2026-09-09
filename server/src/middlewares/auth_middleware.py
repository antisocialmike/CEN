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

security_bearer = HTTPBearer()
BCRYPT_MAX_BYTES = 72

INVALID_TOKEN = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token no valido",
)


def generate_temporary_password() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(
        secrets.choice(alphabet) for _ in range(TEMPORARY_PASSWORD_LENGTH)
    )


def _encode(password: str) -> bytes:
    return password.encode("utf-8")[:BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_encode(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(_encode(password), password_hash.encode("utf-8"))


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    expires_in = expires_delta or timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": datetime.now(timezone.utc) + expires_in})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security_bearer)
) -> dict:
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
    if not username or not role:
        raise INVALID_TOKEN

    return {
        "username": username,
        "role": role,
        "employee_id": payload.get("employee_id"),
    }


def require_role(required_role: str):
    def role_checker(user: dict = Security(get_current_user)) -> dict:
        if user.get("role") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permisos insuficientes",
            )
        return user

    return role_checker
