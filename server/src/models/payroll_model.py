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


class EmployeeUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=3, max_length=150)
    role: EmployeeRole
    base_salary: float = Field(ge=0)


class PayrollCalculationRequest(BaseModel):
    employee_id: int
    period: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    gross_salary: float

    def period_as_date(self) -> date:
        year, month = self.period.split("-")
        return date(int(year), int(month), 1)
