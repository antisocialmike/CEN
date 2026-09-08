from pathlib import Path
from typing import Optional

from ..config.database import db_cursor

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "sql" / "migrations"

CREATE_MIGRATIONS_TABLE = (
    "CREATE TABLE IF NOT EXISTS schema_migrations ("
    "filename VARCHAR(255) PRIMARY KEY, "
    "applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW());"
)
SELECT_APPLIED_MIGRATIONS = "SELECT filename FROM schema_migrations;"
INSERT_MIGRATION = "INSERT INTO schema_migrations (filename) VALUES (%s);"

SELECT_EMPLOYEE_BY_ID = (
    "SELECT id, name, email, role, base_salary "
    "FROM employees WHERE id = %s;"
)
SELECT_EMPLOYEE_BY_EMAIL = (
    "SELECT id, name, email, role, base_salary, password_hash "
    "FROM employees WHERE email = %s;"
)
SELECT_EMPLOYEES = (
    "SELECT id, name, email, role, base_salary "
    "FROM employees ORDER BY name ASC;"
)
INSERT_EMPLOYEE = (
    "INSERT INTO employees (name, email, role, base_salary, password_hash) "
    "VALUES (%s, %s, %s, %s, %s) RETURNING id;"
)
SELECT_RECEIPTS_BY_EMPLOYEE = (
    "SELECT id, employee_id, period, gross_salary, isr_deduction, "
    "imss_deduction, net_salary, processed_by, created_at, updated_at "
    "FROM payroll_receipts WHERE employee_id = %s "
    "ORDER BY period DESC;"
)
SELECT_RECENT_RECEIPTS = (
    "SELECT r.id, r.employee_id, e.name AS employee_name, r.period, "
    "r.gross_salary, r.isr_deduction, r.imss_deduction, r.net_salary, "
    "r.processed_by, r.created_at, r.updated_at "
    "FROM payroll_receipts r JOIN employees e ON e.id = r.employee_id "
    "ORDER BY r.period DESC, r.updated_at DESC LIMIT %s;"
)
UPSERT_RECEIPT = (
    "INSERT INTO payroll_receipts (employee_id, period, gross_salary, "
    "isr_deduction, imss_deduction, net_salary, processed_by) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s) "
    "ON CONFLICT (employee_id, period) DO UPDATE SET "
    "gross_salary = EXCLUDED.gross_salary, "
    "isr_deduction = EXCLUDED.isr_deduction, "
    "imss_deduction = EXCLUDED.imss_deduction, "
    "net_salary = EXCLUDED.net_salary, "
    "processed_by = EXCLUDED.processed_by, "
    "updated_at = NOW() "
    "RETURNING id, (xmax = 0) AS created;"
)


class PayrollRepository:
    def run_migrations(self) -> list:
        applied = []
        with db_cursor() as cursor:
            cursor.execute(CREATE_MIGRATIONS_TABLE)
            cursor.execute(SELECT_APPLIED_MIGRATIONS)
            done = {dict(row)["filename"] for row in cursor.fetchall()}
            for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
                if path.name in done:
                    continue
                cursor.execute(path.read_text(encoding="utf-8"))
                cursor.execute(INSERT_MIGRATION, (path.name,))
                applied.append(path.name)
        return applied

    def get_employee_by_id(self, employee_id: int) -> Optional[dict]:
        return self._fetch_one(SELECT_EMPLOYEE_BY_ID, (employee_id,))

    def get_employee_by_email(self, email: str) -> Optional[dict]:
        return self._fetch_one(SELECT_EMPLOYEE_BY_EMAIL, (email,))

    def list_employees(self) -> list:
        return self._fetch_all(SELECT_EMPLOYEES)

    def create_employee(self, employee_data: dict) -> int:
        return self._insert_returning_id(
            INSERT_EMPLOYEE,
            (
                employee_data["name"],
                employee_data["email"],
                employee_data["role"],
                employee_data["base_salary"],
                employee_data["password_hash"],
            ),
            "No se pudo obtener el ID del empleado.",
        )

    def get_receipts_by_employee_id(self, employee_id: int) -> list:
        return self._fetch_all(SELECT_RECEIPTS_BY_EMPLOYEE, (employee_id,))

    def list_recent_receipts(self, limit: int = 20) -> list:
        return self._fetch_all(SELECT_RECENT_RECEIPTS, (limit,))

    def save_payroll_receipt(self, receipt_data: dict) -> dict:
        with db_cursor() as cursor:
            cursor.execute(
                UPSERT_RECEIPT,
                (
                    receipt_data["employee_id"],
                    receipt_data["period"],
                    receipt_data["gross_salary"],
                    receipt_data["isr_deduction"],
                    receipt_data["imss_deduction"],
                    receipt_data["net_salary"],
                    receipt_data["processed_by"],
                ),
            )
            row = cursor.fetchone()
            if not row:
                raise RuntimeError("No se pudo obtener el ID del recibo.")

            saved = dict(row)
            return {"id": int(saved["id"]), "created": bool(saved["created"])}

    def _fetch_one(self, query: str, params: tuple) -> Optional[dict]:
        with db_cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def _fetch_all(self, query: str, params: tuple = ()) -> list:
        with db_cursor() as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def _insert_returning_id(
        self, query: str, params: tuple, error_message: str
    ) -> int:
        with db_cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            if not row:
                raise RuntimeError(error_message)
            return int(dict(row)["id"])


payroll_repository = PayrollRepository()
