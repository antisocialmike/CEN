from fastapi import APIRouter, Depends, HTTPException
from server.src.models.payroll_model import PayrollCalculationRequest
from server.src.controllers.payroll_controller import PayrollService
from server.src.middlewares.auth_middleware import require_role, get_current_user
from server.src.repositories.payroll_repository import PayrollRepository

router = APIRouter(prefix="/payroll", tags=["Payroll"])
payroll_service = PayrollService()
payroll_repository = PayrollRepository()


@router.post("/calculate")
def calculate_payroll(
    request: PayrollCalculationRequest,
    user: dict = Depends(require_role("admin"))
):
    employee = payroll_repository.get_employee_by_id(request.employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    try:
        breakdown = payroll_service.process_salary(request.gross_salary)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    receipt_id = payroll_repository.save_payroll_receipt({
        "employee_id": request.employee_id,
        "gross_salary": breakdown["gross_salary"],
        "isr_deduction": breakdown["isr_deduction"],
        "imss_deduction": breakdown["imss_deduction"],
        "net_salary": breakdown["net_salary"]
    })

    return {
        "receipt_id": receipt_id,
        "employee_id": request.employee_id,
        "data": breakdown,
        "processed_by": user["username"]
    }


@router.get("/my-receipts")
def get_my_receipts(user: dict = Depends(get_current_user)):
    employee_id = user.get("employee_id")
    if employee_id is None:
        raise HTTPException(status_code=403, detail="Token sin empleado asociado")

    receipts = payroll_repository.get_receipts_by_employee_id(employee_id)
    return {"employee_id": employee_id, "receipts": receipts}
