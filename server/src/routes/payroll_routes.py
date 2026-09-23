from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status

from ..controllers.payroll_controller import PayrollService
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

RECENT_RECEIPTS_LIMIT = 20

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

    try:
        breakdown = payroll_service.process({
            **request.model_dump(exclude={"employee_id", "period_start"}),
            "paid_days": request.paid_days(),
        })
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    try:
        saved = payroll_repository.save_payroll_receipt({
            "employee_id": request.employee_id,
            "company_id": user["company_id"],
            "period_start": request.period_start,
            "period_end": request.period_end(),
            "processed_by": user["username"],
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
def list_recent_receipts(user: dict = Depends(require_admin_company)):
    receipts = payroll_repository.list_recent_receipts(
        user["company_id"], RECENT_RECEIPTS_LIMIT
    )
    return {"receipts": receipts}


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
