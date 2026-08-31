import pytest
from datetime import timedelta
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from server.src.middlewares.auth_middleware import (
    get_current_user,
    create_access_token,
    require_role,
)


def _make_credentials(token: str) -> HTTPAuthorizationCredentials:
    """Crea un objeto de credenciales como el que FastAPI inyectaría
    a partir del header 'Authorization: Bearer <token>'."""
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_get_current_user_invalid_or_expired_token():
    credentials = _make_credentials("token_falso_o_expirado")
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials)
    assert exc_info.value.status_code == 401


def test_get_current_user_token_missing_claims():
    # Token válido pero sin 'sub' ni 'role' en el payload
    token = create_access_token(data={})
    credentials = _make_credentials(token)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials)
    assert exc_info.value.status_code == 401


def test_get_current_user_valid_token():
    token = create_access_token(
        data={"sub": "juan.perez", "role": "admin"},
        expires_delta=timedelta(hours=1),
    )
    credentials = _make_credentials(token)
    user = get_current_user(credentials)
    assert user == {"username": "juan.perez", "role": "admin"}


def test_require_role_allows_matching_role():
    role_checker = require_role("admin")
    user = {"username": "juan.perez", "role": "admin"}
    # role_checker recibe el usuario ya resuelto por get_current_user
    result = role_checker(user=user)
    assert result == user


def test_require_role_rejects_non_matching_role():
    role_checker = require_role("admin")
    user = {"username": "empleado.raso", "role": "employee"}
    with pytest.raises(HTTPException) as exc_info:
        role_checker(user=user)
    assert exc_info.value.status_code == 403