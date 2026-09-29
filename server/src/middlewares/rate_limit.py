import ipaddress
import math
from typing import Optional

from fastapi import HTTPException, Request, status

from ..config.settings import AUTH_RATE_WINDOW_SECONDS, TRUSTED_PROXY_HOPS
from ..repositories.auth_repository import auth_repository


def _minutes(seconds: int) -> int:
    return max(1, math.ceil(seconds / 60))


def _is_address(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def client_address(request: Request, trusted_hops: Optional[int] = None) -> str:
    if trusted_hops is None:
        trusted_hops = TRUSTED_PROXY_HOPS
    peer = request.client.host if request.client else "desconocido"
    if trusted_hops <= 0:
        return peer
    forwarded = [
        hop.strip()
        for hop in request.headers.get("x-forwarded-for", "").split(",")
        if hop.strip()
    ]
    if len(forwarded) < trusted_hops:
        return peer
    candidate = forwarded[-trusted_hops]
    return candidate if _is_address(candidate) else peer


def rate_limit(bucket: str, max_hits: int):

    def check(request: Request) -> None:
        client_key = client_address(request)
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
