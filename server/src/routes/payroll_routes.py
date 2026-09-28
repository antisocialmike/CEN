from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status

from ..controllers.employer_cost import (
    EmployerCostInputs,
    EmployerCostParameters,
    EmployerCostService,
    MissingParameter,
    completed_years,
)
from ..controllers.payroll_controller import (
    MissingPayrollParameter,
    PayrollParameters,
    PayrollService,
    missing_parameter_label,
)
from ..controllers.receipt_pdf import (
    build_receipt_pdf,
    build_receipt_response_headers,
)
from ..middlewares.auth_middleware import get_current_user
from ..middlewares.company_context import (
    COMPANY_HEADER,
    require_admin_company,
    resolve_admin_company,
)
from ..models.pagination_model import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    page_offset,
)
from ..models.payroll_model import (
    PayrollCalculationRequest,
    PeriodLookupRequest,
)
from ..repositories.payroll_repository import (
    ReceiptOfAnotherCompanyError,
    payroll_repository,
)

router = APIRouter(prefix="/payroll", tags=["Payroll"])
payroll_service = PayrollService()
employer_cost_service = EmployerCostService()


def _parameters(request: PayrollCalculationRequest, company_id: int, years: int):
    """Lo vigente al inicio del periodo, la misma fecha que usa el costo patronal:
    los parametros del calculo, los del costo patronal y el SBC que comparten."""
    raw = payroll_repository.employer_cost_parameters(
        company_id, request.period_start
    )
    cost_params = EmployerCostParameters(**raw)
    try:
        payroll_params = PayrollParameters.from_rows(
            raw["rates"], payroll_repository.isr_brackets(request.period_start)
        )
        sbc = employer_cost_service.contribution_base(
            cost_params, request.gross_salary, request.periodicity, years
        )
    except (MissingPayrollParameter, MissingParameter) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "No se puede calcular un periodo que empieza el "
                f"{request.period_start.isoformat()}: no hay "
                f"{missing_parameter_label(error.name)} vigente para esa fecha. "
                "CEN tiene los parametros de 2025 y 2026."
            ),
        ) from error
    return payroll_params, cost_params, sbc


def _employer_cost(
    request: PayrollCalculationRequest, cost_params: EmployerCostParameters,
    years: int, breakdown: dict,
) -> dict:
    return employer_cost_service.calculate(
        EmployerCostInputs(
            period_salary=Decimal(str(request.gross_salary)),
            periodicity=request.periodicity,
            days=Decimal(request.paid_days()),
            years_completed=years,
            total_perceptions=Decimal(str(breakdown["total_perceptions"])),
            worker_imss_paid_by_employer=Decimal(
                str(breakdown["imss_employer_paid"])
            ),
        ),
        cost_params,
    )


RECEIPT_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Recibo no encontrado",
)


@router.post("/calculate")
def calculate_payroll(
    request: PayrollCalculationRequest,
    user: dict = Depends(require_admin_company),
):
    employee = payroll_repository.get_employee_by_id(
        request.employee_id, user["company_id"]
    )
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado",
        )

    if not employee.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede calcular nomina de una cuenta desactivada",
        )

    years = completed_years(employee.get("created_at"), request.period_end())
    payroll_params, cost_params, sbc = _parameters(
        request, user["company_id"], years
    )

    try:
        breakdown = payroll_service.process(
            {
                **request.model_dump(exclude={"employee_id", "period_start"}),
                "paid_days": request.paid_days(),
            },
            payroll_params,
            float(sbc),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    employer_cost = _employer_cost(request, cost_params, years, breakdown)

    try:
        saved = payroll_repository.save_payroll_receipt({
            "employee_id": request.employee_id,
            "company_id": user["company_id"],
            "period_start": request.period_start,
            "period_end": request.period_end(),
            "processed_by": user["username"],
            "employer_cost": employer_cost,
            **breakdown,
        })
    except ReceiptOfAnotherCompanyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ese periodo ya tiene un recibo emitido por otra empresa",
        )
    return {
        "receipt_id": saved["id"],
        "created": saved["created"],
        "employee_id": request.employee_id,
        "employee_name": employee.get("name", ""),
        "period_start": request.period_start.isoformat(),
        "period_end": request.period_end().isoformat(),
        "data": breakdown,
        "employer_cost": {
            "total": employer_cost["total"],
            "sbc_daily": employer_cost["sbc_daily"],
            "missing": employer_cost["missing"],
            "items": employer_cost["items"],
        },
        "processed_by": user["username"],
    }


@router.post("/lookup")
def lookup_receipt(
    request: PeriodLookupRequest,
    user: dict = Depends(require_admin_company),
):
    receipt = payroll_repository.get_receipt_by_period(
        request.employee_id, request.period_start, request.period_end(),
        user["company_id"],
    )
    return {"receipt": receipt}


@router.get("/receipts")
def list_receipts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    user: dict = Depends(require_admin_company),
):
    """El historial de recibos de la empresa, del periodo mas nuevo al mas viejo."""
    receipts, total = payroll_repository.page_receipts(
        user["company_id"], page_size, page_offset(page, page_size)
    )
    return {
        "items": receipts, "total": total, "page": page, "page_size": page_size,
    }


@router.get("/my-receipts")
def get_my_receipts(user: dict = Depends(get_current_user)):
    employee_id = user.get("employee_id")
    if employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token sin empleado asociado",
        )

    receipts = payroll_repository.get_receipts_by_employee_id(employee_id)
    return {"employee_id": employee_id, "receipts": receipts}


@router.get("/receipts/{receipt_id}/pdf")
def download_receipt(
    receipt_id: int,
    user: dict = Depends(get_current_user),
    company_id: Optional[int] = Header(default=None, alias=COMPANY_HEADER),
):
    receipt = payroll_repository.get_receipt_by_id(receipt_id)
    if receipt is None:
        raise RECEIPT_NOT_FOUND

    is_owner = receipt["employee_id"] == user.get("employee_id")
    if not is_owner:
        if user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Este recibo no es tuyo",
            )
        if receipt["company_id"] != resolve_admin_company(user, company_id):
            raise RECEIPT_NOT_FOUND

    return Response(
        content=build_receipt_pdf(receipt),
        media_type="application/pdf",
        headers=build_receipt_response_headers(receipt),
    )
