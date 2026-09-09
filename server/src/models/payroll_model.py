from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

EmployeeRole = Literal["admin", "employee"]


class Employee(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    role: EmployeeRole
    base_salary: float
    is_active: bool = True


class EmployeeCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=3, max_length=150)
    role: EmployeeRole
    base_salary: float = Field(ge=0)
    password: str = Field(min_length=8, max_length=72)


class PasswordResetResponse(BaseModel):
    employee_id: int
    name: str
    email: str
    temporary_password: str


class EmployeeUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=3, max_length=150)
    role: EmployeeRole
    base_salary: float = Field(ge=0)


class PayrollCalculationRequest(BaseModel):
    employee_id: int
    period: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    gross_salary: float
    overtime_double_hours: float = Field(default=0, ge=0, le=744)
    overtime_triple_hours: float = Field(default=0, ge=0, le=744)
    christmas_bonus_days: float = Field(default=0, ge=0, le=90)
    vacation_days: float = Field(default=0, ge=0, le=90)
    bonus: float = Field(default=0, ge=0)
    loan_deduction: float = Field(default=0, ge=0)
    housing_credit_deduction: float = Field(default=0, ge=0)

    def period_as_date(self) -> date:
        year, month = self.period.split("-")
        return date(int(year), int(month), 1)
