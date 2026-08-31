from psycopg2.extras import RealDictCursor
from ..config.database import get_connection

class PayrollRepository:
    def get_employee_by_id(self, employee_id: int) -> dict:
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, name, email, role, base_salary FROM employees WHERE id = %s;", (employee_id,))
                result = cur.fetchone()
                if result is None:
                    return {}
                return dict(result)
        finally:
            conn.close()

    def save_payroll_receipt(self, receipt_data: dict) -> int:
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO payroll_receipts (employee_id, gross_salary, isr_deduction, imss_deduction, net_salary)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id;
                    """,
                    (
                        receipt_data["employee_id"],
                        receipt_data["gross_salary"],
                        receipt_data["isr_deduction"],
                        receipt_data["imss_deduction"],
                        receipt_data["net_salary"]
                    )
                )
                result = cur.fetchone()
                if result is None:
                    raise ValueError("Error inserting payroll receipt")
                receipt_id = result["id"]
                conn.commit()
                return receipt_id
        finally:
            conn.close()