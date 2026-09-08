from typing import Optional

from pydantic import BaseModel

from .payroll_model import EmployeeRole


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: EmployeeRole
    name: str = ""
    employee_id: Optional[int] = None
