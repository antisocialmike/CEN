from datetime import date
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel

from .payroll_model import Periodicity

# Los importes viajan como Decimal y pydantic los manda como texto en JSON:
# asi no se pierden centavos al pasar por float en ningun punto del camino.


class AnalyticsPeriod(BaseModel):
    start: date
    end: date
    previous_start: date
    previous_end: date
    periodicity: Optional[Periodicity] = None


class KpiChange(BaseModel):
    """Variacion porcentual contra el periodo anterior de la misma duracion.

    Es None cuando el periodo anterior no tuvo nada con que comparar.
    """

    gross_payroll: Optional[Decimal] = None
    net_paid: Optional[Decimal] = None
    isr_withheld: Optional[Decimal] = None
    imss_withheld: Optional[Decimal] = None
    paid_employees: Optional[Decimal] = None
    average_cost_per_employee: Optional[Decimal] = None
    employer_cost: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None


class Kpis(BaseModel):
    gross_payroll: Decimal
    net_paid: Decimal
    isr_withheld: Decimal
    imss_withheld: Decimal
    total_deductions: Decimal
    receipts: int
    paid_employees: int
    active_employees: int
    average_cost_per_employee: Optional[Decimal] = None
    employer_cost: Decimal
    # Nomina bruta + costo patronal: lo que la nomina le cuesta a la empresa.
    total_cost: Decimal
    # Costo patronal entre la nomina de los recibos que si lo tienen, x 100.
    employer_cost_pct: Optional[Decimal] = None
    change: KpiChange


class MonthlyPayroll(BaseModel):
    month: date
    gross_payroll: Decimal
    net_paid: Decimal
    isr_withheld: Decimal
    imss_withheld: Decimal
    total_deductions: Decimal
    receipts: int


class ConceptTotal(BaseModel):
    kind: str
    concept: str
    description: str
    amount: Decimal
    taxable: Decimal
    exempt: Decimal


class HeadcountMonth(BaseModel):
    month: date
    hires: int
    terminations: int


class Headcount(BaseModel):
    active: int
    inactive: int
    by_month: List[HeadcountMonth]


class TopSalary(BaseModel):
    id: int
    name: str
    company_name: str
    base_salary: Decimal


class SalaryBucket(BaseModel):
    label: str
    min_salary: Decimal
    max_salary: Optional[Decimal] = None
    employees: int


class CompanyComparison(BaseModel):
    id: int
    legal_name: str
    is_active: bool
    gross_payroll: Decimal
    net_paid: Decimal
    employer_cost: Decimal
    # Nomina bruta + costo patronal, igual que total_cost en los KPI.
    total_cost: Decimal
    receipts: int
    paid_employees: int
    active_employees: int


class EmployerCostCoverage(BaseModel):
    receipts_with_cost: int
    receipts_incomplete: int
    receipts_without_cost: int


class EmployerCostComponent(BaseModel):
    group_key: Literal["imss", "sar", "infonavit", "isn"]
    component: str
    description: str
    amount: Decimal


class MissingParameter(BaseModel):
    name: str
    receipts: int


class EmployerCostMonth(BaseModel):
    month: date
    imss: Decimal
    sar: Decimal
    infonavit: Decimal
    isn: Decimal
    covered_gross: Decimal


class EmployerCost(BaseModel):
    coverage: EmployerCostCoverage
    components: List[EmployerCostComponent]
    missing: List[MissingParameter]
    monthly: List[EmployerCostMonth]


class PayrollAnalytics(BaseModel):
    company_id: Optional[int] = None
    period: AnalyticsPeriod
    kpis: Kpis
    monthly: List[MonthlyPayroll]
    concepts: List[ConceptTotal]
    headcount: Headcount
    top_salaries: List[TopSalary]
    salary_histogram: List[SalaryBucket]
    companies: List[CompanyComparison]
    employer_cost: EmployerCost
