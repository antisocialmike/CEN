import os
from unittest.mock import patch

import pytest

if not os.environ.get("JWT_SECRET_KEY"):
    os.environ["JWT_SECRET_KEY"] = "clave-solo-para-tests"

AUTH_REPOSITORY = "server.src.repositories.auth_repository.auth_repository"


def active_session(**overrides) -> dict:
    state = {
        "same_role": True,
        "is_active": True,
        "must_change_password": False,
        "token_version": 0,
        "company_is_active": None,
    }
    state.update(overrides)
    return state


@pytest.fixture(autouse=True)
def session_state():
    with patch(AUTH_REPOSITORY + ".session_state") as state:
        state.return_value = active_session()
        yield state


@pytest.fixture(autouse=True)
def rate_limit_window():
    with patch(AUTH_REPOSITORY + ".hit_rate_limit") as hit:
        hit.return_value = {"hits": 1, "retry_after": 900}
        yield hit
