from fastapi import APIRouter, Depends, HTTPException, Response, status

from ..controllers.payroll_controller import PayrollService
from ..controllers.receipt_pdf import (
    build_receipt_pdf,
    build_receipt_response_headers,
)
from ..middlewares.auth_middleware import get_current_user, require_role
from ..models.payroll_model import PayrollCalculationRequest
from ..repositories.payroll_repository import payroll_repository

router = APIRouter(prefix="/payroll", tags=["Payroll"])
payroll_service = PayrollService()

RECENT_RECEIPTS_LIMIT = 20


@router.post("/calculate")
def calculate_payroll(
    request: PayrollCalculationRequest,
    user: dict = Depends(require_role("admin")),
):
    employee = payroll_repository.get_employee_by_id(request.employee_id)
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

    saved = payroll_repository.save_payroll_receipt({
        "employee_id": request.employee_id,
        "period_start": request.period_start,
        "period_end": request.period_end(),
        "processed_by": user["username"],
        **breakdown,
    })
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


@router.get("/receipts")
def list_recent_receipts(user: dict = Depends(require_role("admin"))):
    receipts = payroll_repository.list_recent_receipts(RECENT_RECEIPTS_LIMIT)
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
):
    receipt = payroll_repository.get_receipt_by_id(receipt_id)
    if receipt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recibo no encontrado",
        )

    is_owner = receipt["employee_id"] == user.get("employee_id")
    if user.get("role") != "admin" and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este recibo no es tuyo",
        )

    return Response(
        content=build_receipt_pdf(receipt),
        media_type="application/pdf",
        headers=build_receipt_response_headers(receipt),
    )
