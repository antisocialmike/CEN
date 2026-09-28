import math

from fastapi import HTTPException, Request, status

from ..config.settings import AUTH_RATE_WINDOW_SECONDS
from ..repositories.auth_repository import auth_repository


def _minutes(seconds: int) -> int:
    return max(1, math.ceil(seconds / 60))


def rate_limit(bucket: str, max_hits: int):

    def check(request: Request) -> None:
        client_key = request.client.host if request.client else "desconocido"
        window = auth_repository.hit_rate_limit(
            bucket, client_key, AUTH_RATE_WINDOW_SECONDS
        )
        if window["hits"] > max_hits:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiadas solicitudes desde tu conexion. "
                "Vuelve a intentarlo en {} minutos".format(
                    _minutes(window["retry_after"])
                ),
                headers={"Retry-After": str(window["retry_after"])},
            )

    return check
