import pytest
from datetime import timedelta
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from server.src.middlewares.auth_middleware import (
    get_current_user,
    get_user_changing_password,
    create_access_token,
    generate_temporary_password,
    hash_reset_code,
    require_role,
    hash_password,
    reset_code_matches,
    verify_password,
)
from server.tests.conftest import active_session


def _make_credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_get_current_user_invalid_or_expired_token():
    credentials = _make_credentials("token_falso_o_expirado")
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials)
    assert exc_info.value.status_code == 401


def test_get_current_user_token_missing_claims():
    token = create_access_token(data={})
    credentials = _make_credentials(token)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials)
    assert exc_info.value.status_code == 401


def test_get_current_user_valid_token():
    token = create_access_token(
        data={"sub": "juan.perez", "role": "admin", "employee_id": 1},
        expires_delta=timedelta(hours=1),
    )
    credentials = _make_credentials(token)
    user = get_current_user(credentials)
    assert user == {
        "username": "juan.perez", "role": "admin", "employee_id": 1,
        "company_id": None,
    }


def _credentials_for(**claims) -> HTTPAuthorizationCredentials:
    data = {"sub": "ana@cen.com", "role": "employee", "employee_id": 7}
    data.update(claims)
    return _make_credentials(create_access_token(data=data))


def test_get_current_user_checks_the_account_behind_the_token(session_state):
    get_current_user(_credentials_for(role="admin", employee_id=3))

    session_state.assert_called_once_with(3, "admin")


@pytest.mark.parametrize("state", [
    {"is_active": False},
    {"same_role": False},
    {"company_is_active": False},
    {"token_version": 1},
])
def test_get_current_user_rejects_revoked_sessions(state, session_state):
    session_state.return_value = active_session(**state)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(_credentials_for())
    assert exc_info.value.status_code == 401


def test_get_current_user_rejects_an_account_that_no_longer_exists(session_state):
    session_state.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(_credentials_for())
    assert exc_info.value.status_code == 401


def test_get_current_user_accepts_the_current_version(session_state):
    session_state.return_value = active_session(token_version=4)

    user = get_current_user(_credentials_for(ver=4))

    assert user["employee_id"] == 7


def test_get_current_user_rejects_tokens_without_an_account():
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(_make_credentials(
            create_access_token(data={"sub": "admin1", "role": "admin"})
        ))
    assert exc_info.value.status_code == 401


def test_a_temporary_password_only_lets_you_change_it(session_state):
    session_state.return_value = active_session(must_change_password=True)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(_credentials_for())
    assert exc_info.value.status_code == 403
    assert "temporal" in exc_info.value.detail

    user = get_user_changing_password(_credentials_for())
    assert user["employee_id"] == 7


def test_require_role_allows_matching_role():
    role_checker = require_role("admin")
    user = {"username": "juan.perez", "role": "admin"}
    result = role_checker(user=user)
    assert result == user


def test_require_role_rejects_non_matching_role():
    role_checker = require_role("admin")
    user = {"username": "empleado.raso", "role": "employee"}
    with pytest.raises(HTTPException) as exc_info:
        role_checker(user=user)
    assert exc_info.value.status_code == 403


def test_hash_password_and_verify_password():
    password_hash = hash_password("clave123")
    assert password_hash != "clave123"
    assert verify_password("clave123", password_hash)
    assert not verify_password("otra_clave", password_hash)


def test_reset_codes_are_stored_as_a_keyed_hash():
    code_hash = hash_reset_code("123456")

    assert code_hash != "123456"
    assert len(code_hash) == 64
    assert reset_code_matches("123456", code_hash)
    assert not reset_code_matches("123457", code_hash)


def test_generate_temporary_password_is_long_and_random():
    first = generate_temporary_password()
    second = generate_temporary_password()

    assert len(first) >= 8
    assert first != second
    assert first.isalnum()


def test_generate_temporary_password_avoids_ambiguous_characters():
    passwords = "".join(generate_temporary_password() for _ in range(200))

    assert not set(passwords) & set("0O1lI")
