from pydantic import BaseModel
from typing import Optional


class PayrollCalculationRequest(BaseModel):
    employee_id: int
    gross_salary: float


class PayrollReceipt(BaseModel):
    receipt_id: Optional[int] = None
    employee_id: int
    gross_salary: float
    isr_deduction: float
    imss_deduction: float
    net_salary: float
