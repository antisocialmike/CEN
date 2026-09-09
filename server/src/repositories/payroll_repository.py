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
    "SELECT id, name, email, role, base_salary, is_active "
    "FROM employees WHERE id = %s;"
)
SELECT_EMPLOYEE_BY_EMAIL = (
    "SELECT id, name, email, role, base_salary, password_hash, "
    "must_change_password, is_active, failed_login_attempts, locked_until "
    "FROM employees WHERE email = %s;"
)
REGISTER_FAILED_LOGIN = (
    "UPDATE employees SET failed_login_attempts = failed_login_attempts + 1, "
    "locked_until = CASE WHEN failed_login_attempts + 1 >= %s "
    "THEN NOW() + make_interval(mins => %s) ELSE locked_until END "
    "WHERE id = %s RETURNING failed_login_attempts, locked_until;"
)
CLEAR_FAILED_LOGINS = (
    "UPDATE employees SET failed_login_attempts = 0, locked_until = NULL "
    "WHERE id = %s;"
)
RESET_PASSWORD = (
    "UPDATE employees SET password_hash = %s, must_change_password = TRUE, "
    "failed_login_attempts = 0, locked_until = NULL WHERE id = %s "
    "RETURNING id, name, email, role, base_salary, is_active;"
)
SELECT_PASSWORD_HASH = (
    "SELECT password_hash FROM employees WHERE id = %s;"
)
UPDATE_PASSWORD = (
    "UPDATE employees SET password_hash = %s, must_change_password = FALSE "
    "WHERE id = %s;"
)
SELECT_EMPLOYEES = (
    "SELECT id, name, email, role, base_salary, is_active "
    "FROM employees ORDER BY is_active DESC, name ASC;"
)
UPDATE_EMPLOYEE = (
    "UPDATE employees SET name = %s, email = %s, role = %s, base_salary = %s "
    "WHERE id = %s RETURNING id, name, email, role, base_salary, is_active;"
)
UPDATE_EMPLOYEE_ACTIVE = (
    "UPDATE employees SET is_active = %s WHERE id = %s "
    "RETURNING id, name, email, role, base_salary, is_active;"
)
INSERT_EMPLOYEE = (
    "INSERT INTO employees (name, email, role, base_salary, password_hash, "
    "must_change_password) VALUES (%s, %s, %s, %s, %s, TRUE) RETURNING id;"
)
RECEIPT_ITEMS_JSON = (
    "COALESCE(json_agg(json_build_object("
    "'kind', i.kind, 'concept', i.concept, "
    "'description', i.description, 'amount', i.amount, "
    "'taxable', i.taxable, 'exempt', i.exempt) "
    "ORDER BY i.position) FILTER (WHERE i.id IS NOT NULL), '[]') AS items "
)

SELECT_RECEIPTS_BY_EMPLOYEE = (
    "SELECT r.id, r.employee_id, r.period, r.gross_salary, r.isr_deduction, "
    "r.imss_deduction, r.net_salary, r.total_perceptions, "
    "r.total_deductions, r.taxable_base, r.periodicity, r.paid_days, "
    "r.processed_by, r.created_at, "
    "r.updated_at, "
    + RECEIPT_ITEMS_JSON
    + "FROM payroll_receipts r "
    "LEFT JOIN payroll_receipt_items i ON i.receipt_id = r.id "
    "WHERE r.employee_id = %s GROUP BY r.id ORDER BY r.period_start DESC;"
)
SELECT_RECENT_RECEIPTS = (
    "SELECT r.id, r.employee_id, e.name AS employee_name, "
    "r.period_start, r.period_end, r.periodicity, r.paid_days, "
    "r.gross_salary, r.isr_deduction, r.imss_deduction, r.net_salary, "
    "r.total_perceptions, r.total_deductions, r.taxable_base, "
    "r.processed_by, r.created_at, r.updated_at, "
    + RECEIPT_ITEMS_JSON
    + "FROM payroll_receipts r JOIN employees e ON e.id = r.employee_id "
    "LEFT JOIN payroll_receipt_items i ON i.receipt_id = r.id "
    "GROUP BY r.id, e.name "
    "ORDER BY r.period_start DESC, r.updated_at DESC LIMIT %s;"
)
SELECT_RECEIPT_BY_ID = (
    "SELECT r.id, r.employee_id, e.name AS employee_name, "
    "e.email AS employee_email, r.period_start, r.period_end, "
    "r.gross_salary, r.isr_deduction, "
    "r.imss_deduction, r.net_salary, r.total_perceptions, "
    "r.total_deductions, r.taxable_base, r.periodicity, r.paid_days, "
    "r.processed_by, r.created_at, "
    + RECEIPT_ITEMS_JSON
    + "FROM payroll_receipts r JOIN employees e ON e.id = r.employee_id "
    "LEFT JOIN payroll_receipt_items i ON i.receipt_id = r.id "
    "WHERE r.id = %s GROUP BY r.id, e.name, e.email;"
)
UPSERT_RECEIPT = (
    "INSERT INTO payroll_receipts (employee_id, period_start, period_end, "
    "periodicity, paid_days, gross_salary, isr_deduction, imss_deduction, "
    "net_salary, total_perceptions, total_deductions, taxable_base, "
    "processed_by) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
    "ON CONFLICT (employee_id, period_start, period_end) DO UPDATE SET "
    "periodicity = EXCLUDED.periodicity, "
    "paid_days = EXCLUDED.paid_days, "
    "gross_salary = EXCLUDED.gross_salary, "
    "isr_deduction = EXCLUDED.isr_deduction, "
    "imss_deduction = EXCLUDED.imss_deduction, "
    "net_salary = EXCLUDED.net_salary, "
    "total_perceptions = EXCLUDED.total_perceptions, "
    "total_deductions = EXCLUDED.total_deductions, "
    "taxable_base = EXCLUDED.taxable_base, "
    "processed_by = EXCLUDED.processed_by, "
    "updated_at = NOW() "
    "RETURNING id, (xmax = 0) AS created;"
)
DELETE_RECEIPT_ITEMS = (
    "DELETE FROM payroll_receipt_items WHERE receipt_id = %s;"
)
INSERT_RECEIPT_ITEM = (
    "INSERT INTO payroll_receipt_items (receipt_id, kind, concept, "
    "description, amount, taxable, exempt, position) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"
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

    def update_employee(
        self, employee_id: int, employee_data: dict
    ) -> Optional[dict]:
        return self._fetch_one(
            UPDATE_EMPLOYEE,
            (
                employee_data["name"],
                employee_data["email"],
                employee_data["role"],
                employee_data["base_salary"],
                employee_id,
            ),
        )

    def set_employee_active(
        self, employee_id: int, is_active: bool
    ) -> Optional[dict]:
        return self._fetch_one(UPDATE_EMPLOYEE_ACTIVE, (is_active, employee_id))

    def get_password_hash(self, employee_id: int) -> Optional[str]:
        row = self._fetch_one(SELECT_PASSWORD_HASH, (employee_id,))
        return row["password_hash"] if row else None

    def register_failed_login(
        self, employee_id: int, max_attempts: int, lock_minutes: int
    ) -> Optional[dict]:
        return self._fetch_one(
            REGISTER_FAILED_LOGIN, (max_attempts, lock_minutes, employee_id)
        )

    def clear_failed_logins(self, employee_id: int) -> None:
        with db_cursor() as cursor:
            cursor.execute(CLEAR_FAILED_LOGINS, (employee_id,))

    def reset_password(
        self, employee_id: int, password_hash: str
    ) -> Optional[dict]:
        return self._fetch_one(RESET_PASSWORD, (password_hash, employee_id))

    def update_password(self, employee_id: int, password_hash: str) -> None:
        with db_cursor() as cursor:
            cursor.execute(UPDATE_PASSWORD, (password_hash, employee_id))

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

    def get_receipt_by_id(self, receipt_id: int) -> Optional[dict]:
        return self._fetch_one(SELECT_RECEIPT_BY_ID, (receipt_id,))

    def list_recent_receipts(self, limit: int = 20) -> list:
        return self._fetch_all(SELECT_RECENT_RECEIPTS, (limit,))

    def save_payroll_receipt(self, receipt_data: dict) -> dict:
        with db_cursor() as cursor:
            cursor.execute(
                UPSERT_RECEIPT,
                (
                    receipt_data["employee_id"],
                    receipt_data["period_start"],
                    receipt_data["period_end"],
                    receipt_data["periodicity"],
                    receipt_data["paid_days"],
                    receipt_data["gross_salary"],
                    receipt_data["isr_deduction"],
                    receipt_data["imss_deduction"],
                    receipt_data["net_salary"],
                    receipt_data["total_perceptions"],
                    receipt_data["total_deductions"],
                    receipt_data["taxable_base"],
                    receipt_data["processed_by"],
                ),
            )
            row = cursor.fetchone()
            if not row:
                raise RuntimeError("No se pudo obtener el ID del recibo.")

            saved = dict(row)
            receipt_id = int(saved["id"])

            cursor.execute(DELETE_RECEIPT_ITEMS, (receipt_id,))
            for position, item in enumerate(receipt_data.get("items", [])):
                cursor.execute(INSERT_RECEIPT_ITEM, (
                    receipt_id,
                    item["kind"],
                    item["concept"],
                    item["description"],
                    item["amount"],
                    item["taxable"],
                    item["exempt"],
                    position,
                ))

            return {"id": receipt_id, "created": bool(saved["created"])}

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
