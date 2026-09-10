from calendar import monthrange
from datetime import date, timedelta
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

EmployeeRole = Literal["admin", "employee"]
Periodicity = Literal["mensual", "quincenal", "semanal"]


def period_start_is_valid(periodicity: str, start: date) -> bool:
    if periodicity == "mensual":
        return start.day == 1
    if periodicity == "quincenal":
        return start.day in (1, 16)
    return True


def period_end_for(periodicity: str, start: date) -> date:
    last_day = monthrange(start.year, start.month)[1]
    if periodicity == "mensual":
        return start.replace(day=last_day)
    if periodicity == "quincenal":
        if start.day == 1:
            return start.replace(day=15)
        return start.replace(day=last_day)
    return start + timedelta(days=6)


def paid_days_for(periodicity: str, start: date) -> int:
    return (period_end_for(periodicity, start) - start).days + 1


PERIOD_START_ERRORS = {
    "mensual": "Un periodo mensual empieza el dia 1",
    "quincenal": "Una quincena empieza el dia 1 o el 16",
}


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
        if not period_start_is_valid(self.periodicity, self.period_start):
            raise ValueError(PERIOD_START_ERRORS[self.periodicity])
        return self

    def period_end(self) -> date:
        return period_end_for(self.periodicity, self.period_start)

    def paid_days(self) -> int:
        return paid_days_for(self.periodicity, self.period_start)


class PeriodLookupRequest(BaseModel):
    employee_id: int
    periodicity: Periodicity
    period_start: date

    @model_validator(mode="after")
    def _check_period_start(self) -> "PeriodLookupRequest":
        if not period_start_is_valid(self.periodicity, self.period_start):
            raise ValueError(PERIOD_START_ERRORS[self.periodicity])
        return self

    def period_end(self) -> date:
        return period_end_for(self.periodicity, self.period_start)
