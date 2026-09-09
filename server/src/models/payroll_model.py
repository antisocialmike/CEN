from calendar import monthrange
from datetime import date, timedelta
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

EmployeeRole = Literal["admin", "employee"]
Periodicity = Literal["mensual", "quincenal", "semanal"]


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
    periodicity: Periodicity = "mensual"
    period_start: date
    gross_salary: float
    overtime_double_hours: float = Field(default=0, ge=0, le=744)
    overtime_triple_hours: float = Field(default=0, ge=0, le=744)
    christmas_bonus_days: float = Field(default=0, ge=0, le=90)
    vacation_days: float = Field(default=0, ge=0, le=90)
    bonus: float = Field(default=0, ge=0)
    loan_deduction: float = Field(default=0, ge=0)
    housing_credit_deduction: float = Field(default=0, ge=0)

    @model_validator(mode="after")
    def _check_period_start(self) -> "PayrollCalculationRequest":
        day = self.period_start.day
        if self.periodicity == "mensual" and day != 1:
            raise ValueError("Un periodo mensual empieza el dia 1")
        if self.periodicity == "quincenal" and day not in (1, 16):
            raise ValueError("Una quincena empieza el dia 1 o el 16")
        return self

    def period_end(self) -> date:
        last_day = monthrange(self.period_start.year, self.period_start.month)[1]
        if self.periodicity == "mensual":
            return self.period_start.replace(day=last_day)
        if self.periodicity == "quincenal":
            if self.period_start.day == 1:
                return self.period_start.replace(day=15)
            return self.period_start.replace(day=last_day)
        return self.period_start + timedelta(days=6)

    def paid_days(self) -> int:
        return (self.period_end() - self.period_start).days + 1
