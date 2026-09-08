from fastapi import APIRouter, Depends, HTTPException, status

from ..controllers.payroll_controller import PayrollService
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

    try:
        breakdown = payroll_service.process_salary(request.gross_salary)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    saved = payroll_repository.save_payroll_receipt({
        "employee_id": request.employee_id,
        "period": request.period_as_date(),
        "processed_by": user["username"],
        **breakdown,
    })
    return {
        "receipt_id": saved["id"],
        "created": saved["created"],
        "employee_id": request.employee_id,
        "employee_name": employee.get("name", ""),
        "period": request.period,
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
