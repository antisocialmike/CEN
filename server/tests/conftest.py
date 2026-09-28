import os
from unittest.mock import patch

import pytest

if not os.environ.get("JWT_SECRET_KEY"):
    os.environ["JWT_SECRET_KEY"] = "clave-solo-para-tests"

AUTH_REPOSITORY = "server.src.repositories.auth_repository.auth_repository"


def active_session(**overrides) -> dict:
    """La cuenta de un token vigente: activa, con el rol del token, sin
    contrasena temporal y con la version de sesion con la que se emitio."""
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
    # Cada peticion autenticada consulta la cuenta. Las pruebas no tienen base:
    # por omision todo token es de una cuenta al dia, y quien pruebe la
    # revocacion cambia lo que devuelve este doble.
    with patch(AUTH_REPOSITORY + ".session_state") as state:
        state.return_value = active_session()
        yield state


@pytest.fixture(autouse=True)
def rate_limit_window():
    # Lo mismo con el limite por direccion: por omision, la primera solicitud
    # de una ventana recien abierta.
    with patch(AUTH_REPOSITORY + ".hit_rate_limit") as hit:
        hit.return_value = {"hits": 1, "retry_after": 900}
        yield hit
