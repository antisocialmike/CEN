from typing import Literal, Optional

from pydantic import BaseModel, Field

from .email_address import EmailAddress

UserRole = Literal["superadmin", "owner", "admin", "employee"]


class LoginRequest(BaseModel):
    email: EmailAddress
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    name: str = ""
    employee_id: Optional[int] = None
    must_change_password: bool = False


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)


class PasswordChangeResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PasswordResetRequest(BaseModel):
    email: EmailAddress


class PasswordResetVerify(BaseModel):
    email: EmailAddress
    code: str = Field(pattern=r"^[0-9]{6}$")
    new_password: str = Field(min_length=8, max_length=72)
