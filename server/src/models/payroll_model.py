from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from .fiscal_ids import (
    birth_dates_match,
    validate_curp,
    validate_nss,
    validate_rfc,
)

EmployeeRole = Literal["admin", "employee"]
Periodicity = Literal["mensual", "quincenal", "semanal"]
# Claves de los catalogos del SAT (c_TipoRegimen y c_TipoJornada): 02 Sueldos,
# 09 Asimilados honorarios; 01 Diurna, 02 Nocturna, 03 Mixta.
TipoRegimen = Literal["02", "09"]
TipoJornada = Literal["01", "02", "03"]


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


def next_period_start(periodicity: str, start: date) -> date:
    """El periodo que sigue, con los cortes que ofrece la calculadora del
    admin: meses, quincenas del 1 y del 16, y semanas que empiezan el 1, 8,
    15, 22 y 29 de cada mes."""
    last_day = monthrange(start.year, start.month)[1]
    if periodicity == "quincenal" and start.day < 16:
        return start.replace(day=16)
    if periodicity == "semanal" and start.day + 7 <= last_day:
        return start + timedelta(days=7)
    # Del dia 1 mas 31 dias siempre se cae en el mes siguiente.
    return (start.replace(day=1) + timedelta(days=31)).replace(day=1)


PERIOD_START_ERRORS = {
    "mensual": "Un periodo mensual empieza el dia 1",
    "quincenal": "Una quincena empieza el dia 1 o el 16",
}


class Employee(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    role: EmployeeRole
    # Vacio para los admins que invita un dueno: operan la nomina, no la cobran.
    base_salary: Optional[float] = None
    is_active: bool = True
    tipo_regimen: TipoRegimen = "02"
    tipo_jornada: TipoJornada = "01"
    hire_date: Optional[date] = None
    rfc: Optional[str] = None
    curp: Optional[str] = None
    nss: Optional[str] = None


class FiscalIds(BaseModel):
    rfc: Optional[str] = None
    curp: Optional[str] = None
    nss: Optional[str] = None

    @field_validator("rfc")
    @classmethod
    def _valid_rfc(cls, value: Optional[str]) -> Optional[str]:
        return validate_rfc(value)

    @field_validator("curp")
    @classmethod
    def _valid_curp(cls, value: Optional[str]) -> Optional[str]:
        return validate_curp(value)

    @field_validator("nss")
    @classmethod
    def _valid_nss(cls, value: Optional[str]) -> Optional[str]:
        return validate_nss(value)

    @model_validator(mode="after")
    def _same_birth_date(self) -> "FiscalIds":
        if not birth_dates_match(self.rfc, self.curp):
            raise ValueError(
                "El RFC y la CURP no tienen la misma fecha de nacimiento"
            )
        return self


class SalaryChange(BaseModel):
    base_salary: float
    valid_from: date
    recorded_at: datetime
    recorded_by: Optional[str] = None


class EmployeeCreateRequest(FiscalIds):
    name: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=3, max_length=150)
    role: EmployeeRole
    base_salary: float = Field(ge=0)
    password: str = Field(min_length=8, max_length=72)
    tipo_regimen: TipoRegimen = "02"
    tipo_jornada: TipoJornada = "01"
    hire_date: Optional[date] = None


class PasswordResetResponse(BaseModel):
    employee_id: int
    name: str
    email: str
    temporary_password: str


class EmployeeUpdateRequest(FiscalIds):
    name: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=3, max_length=150)
    role: EmployeeRole
    base_salary: Optional[float] = Field(default=None, ge=0)
    tipo_regimen: TipoRegimen = "02"
    tipo_jornada: TipoJornada = "01"
    hire_date: Optional[date] = None
    salary_valid_from: Optional[date] = None

    @model_validator(mode="after")
    def _employees_have_a_salary(self) -> "EmployeeUpdateRequest":
        if self.role == "employee" and self.base_salary is None:
            raise ValueError("Un empleado necesita salario base")
        return self


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
