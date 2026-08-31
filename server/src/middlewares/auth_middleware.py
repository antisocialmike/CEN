from datetime import datetime, timedelta, timezone
from typing import Optional, cast
from jose import JWTError, jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

SECRET_KEY = "cen-secret-payroll-key-for-jwt-tokens"
ALGORITHM = "HS256"
security_bearer = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=8))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security_bearer)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = cast(str, payload.get("sub"))
        role: str = cast(str, payload.get("role"))
        if username is None or role is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no valido")
        return {"username": username, "role": role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no valido")


def require_role(required_role: str):
    def role_checker(user: dict = Security(get_current_user)):
        if user.get("role") != required_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Permisos insuficientes")
        return user
    return role_checker
