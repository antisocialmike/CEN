from typing import Optional

from pydantic import BaseModel, Field

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
    must_change_password: bool = False


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)
