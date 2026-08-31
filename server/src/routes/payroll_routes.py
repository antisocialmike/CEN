from fastapi import APIRouter, Depends, HTTPException
from ..models.payroll_model import PayrollCalculationRequest
from ..controllers.payroll_controller import PayrollService
from ..middlewares.auth_middleware import require_role

router = APIRouter(prefix="/payroll", tags=["Payroll"])
payroll_service = PayrollService()


@router.post("/calculate")
def calculate_payroll(request: PayrollCalculationRequest, user: dict = Depends(require_role("admin"))):
    try:
        breakdown = payroll_service.process_salary(request.gross_salary)
        return {
            "employee_id": request.employee_id,
            "data": breakdown,
            "processed_by": user["username"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
