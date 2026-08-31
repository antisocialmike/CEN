from typing import Optional
from ..config.database import get_connection


class PayrollRepository:
    def get_employee_by_id(self, employee_id: int) -> Optional[dict]:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                query = (
                    "SELECT id, name, email, role, base_salary "
                    "FROM employees WHERE id = %s;"
                )
                cur.execute(query, (employee_id,))
                row = cur.fetchone()
                return dict(row) if row else None
        finally:
            conn.close()

    def save_payroll_receipt(self, receipt_data: dict) -> int:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                insert_query = (
                    "INSERT INTO payroll_receipts ("
                    "employee_id, gross_salary, isr_deduction, "
                    "imss_deduction, net_salary) "
                    "VALUES (%s, %s, %s, %s, %s) RETURNING id;"
                )
                cur.execute(
                    insert_query,
                    (
                        receipt_data["employee_id"],
                        receipt_data["gross_salary"],
                        receipt_data["isr_deduction"],
                        receipt_data["imss_deduction"],
                        receipt_data["net_salary"]
                    )
                )
                
                row = cur.fetchone()
                if not row:
                    raise RuntimeError("No se pudo obtener el ID del recibo.")
                
                row_dict = dict(row)
                receipt_id = int(row_dict["id"])
                
                conn.commit()
                return receipt_id
        finally:
            conn.close()