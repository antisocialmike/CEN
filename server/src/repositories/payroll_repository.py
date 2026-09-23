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

# Una persona pertenece a la empresa si es su empleado o si la administra con
# una asignacion activa. Los duenos y el superadmin nunca entran aqui.
SELECT_EMPLOYEE_BY_ID = (
    "SELECT e.id, e.name, e.email, e.role, e.base_salary, e.is_active "
    "FROM employees e WHERE e.id = %s "
    "AND e.role IN ('admin', 'employee') AND (e.company_id = %s OR EXISTS ("
    "SELECT 1 FROM company_admins ca WHERE ca.admin_id = e.id "
    "AND ca.company_id = %s AND ca.is_active));"
)
SELECT_EMPLOYEE_BY_EMAIL = (
    "SELECT e.id, e.name, e.email, e.role, e.base_salary, e.password_hash, "
    "e.must_change_password, e.is_active, e.failed_login_attempts, "
    "e.locked_until, e.company_id, c.is_active AS company_is_active "
    "FROM employees e LEFT JOIN companies c ON c.id = e.company_id "
    "WHERE e.email = %s;"
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
    "SELECT e.id, e.name, e.email, e.role, e.base_salary, e.is_active "
    "FROM employees e WHERE e.role IN ('admin', 'employee') "
    "AND (e.company_id = %s OR EXISTS ("
    "SELECT 1 FROM company_admins ca WHERE ca.admin_id = e.id "
    "AND ca.company_id = %s AND ca.is_active)) "
    "ORDER BY e.is_active DESC, e.name ASC;"
)
# Bloquea a la persona mientras se modifica y dice si tambien administra
# otras empresas: en ese caso la cuenta no es solo de esta empresa.
LOCK_MEMBER = (
    "SELECT e.id, e.role, EXISTS ("
    "SELECT 1 FROM company_admins other WHERE other.admin_id = e.id "
    "AND other.company_id <> %s AND other.is_active) AS is_shared "
    "FROM employees e WHERE e.id = %s "
    "AND e.role IN ('admin', 'employee') AND (e.company_id = %s OR EXISTS ("
    "SELECT 1 FROM company_admins ca WHERE ca.admin_id = e.id "
    "AND ca.company_id = %s AND ca.is_active)) FOR UPDATE OF e;"
)
UPDATE_EMPLOYEE = (
    "UPDATE employees SET name = %s, email = %s, role = %s, "
    "base_salary = %s, company_id = %s WHERE id = %s "
    "RETURNING id, name, email, role, base_salary, is_active;"
)
ASSIGN_ADMIN = (
    "INSERT INTO company_admins (admin_id, company_id, assigned_by) "
    "VALUES (%s, %s, %s) ON CONFLICT (admin_id, company_id) "
    "DO UPDATE SET is_active = TRUE;"
)
RELEASE_ADMIN = (
    "UPDATE company_admins SET is_active = FALSE WHERE admin_id = %s;"
)
UPDATE_EMPLOYEE_ACTIVE = (
    "UPDATE employees SET is_active = %s WHERE id = %s "
    "RETURNING id, name, email, role, base_salary, is_active;"
)
INSERT_EMPLOYEE = (
    "INSERT INTO employees (name, email, role, base_salary, password_hash, "
    "must_change_password, company_id) "
    "VALUES (%s, %s, %s, %s, %s, TRUE, %s) RETURNING id;"
)
SELECT_FIRST_COMPANY = "SELECT id FROM companies ORDER BY id LIMIT 1;"
RECEIPT_ITEMS_JSON = (
    "COALESCE(json_agg(json_build_object("
    "'kind', i.kind, 'concept', i.concept, "
    "'description', i.description, 'amount', i.amount, "
    "'taxable', i.taxable, 'exempt', i.exempt) "
    "ORDER BY i.position) FILTER (WHERE i.id IS NOT NULL), '[]') AS items "
)

SELECT_RECEIPTS_BY_EMPLOYEE = (
    "SELECT r.id, r.employee_id, r.period_start, r.period_end, "
    "r.gross_salary, r.isr_deduction, "
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
    "WHERE r.company_id = %s GROUP BY r.id, e.name "
    "ORDER BY r.period_start DESC, r.updated_at DESC LIMIT %s;"
)
SELECT_RECEIPT_BY_ID = (
    "SELECT r.id, r.employee_id, e.name AS employee_name, "
    "e.email AS employee_email, r.company_id, "
    "r.period_start, r.period_end, "
    "r.gross_salary, r.isr_deduction, "
    "r.imss_deduction, r.net_salary, r.total_perceptions, "
    "r.total_deductions, r.taxable_base, r.periodicity, r.paid_days, "
    "r.processed_by, r.created_at, "
    + RECEIPT_ITEMS_JSON
    + "FROM payroll_receipts r JOIN employees e ON e.id = r.employee_id "
    "LEFT JOIN payroll_receipt_items i ON i.receipt_id = r.id "
    "WHERE r.id = %s GROUP BY r.id, e.name, e.email;"
)
SELECT_RECEIPT_BY_PERIOD = (
    "SELECT id, employee_id, period_start, period_end, periodicity, "
    "net_salary, total_perceptions, total_deductions, processed_by, "
    "created_at, updated_at FROM payroll_receipts "
    "WHERE employee_id = %s AND period_start = %s AND period_end = %s "
    "AND company_id = %s;"
)
UPSERT_RECEIPT = (
    "INSERT INTO payroll_receipts (employee_id, period_start, period_end, "
    "periodicity, paid_days, gross_salary, isr_deduction, imss_deduction, "
    "net_salary, total_perceptions, total_deductions, taxable_base, "
    "processed_by, company_id) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
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
    "WHERE payroll_receipts.company_id = EXCLUDED.company_id "
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
INSERT_PASSWORD_RESET_TOKEN = (
    "INSERT INTO password_reset_tokens (employee_id, token, code, expires_at) "
    "VALUES (%s, %s, %s, %s);"
)
SELECT_PASSWORD_RESET_TOKEN = (
    "SELECT id, employee_id, token, code, created_at, expires_at, used_at "
    "FROM password_reset_tokens WHERE code = %s;"
)
MARK_RESET_TOKEN_USED = (
    "UPDATE password_reset_tokens SET used_at = NOW() WHERE id = %s;"
)


class SharedAdminError(Exception):
    pass


class ReceiptOfAnotherCompanyError(Exception):
    pass


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

    def get_employee_by_id(
        self, employee_id: int, company_id: int
    ) -> Optional[dict]:
        return self._fetch_one(
            SELECT_EMPLOYEE_BY_ID, (employee_id, company_id, company_id)
        )

    def get_employee_by_email(self, email: str) -> Optional[dict]:
        return self._fetch_one(SELECT_EMPLOYEE_BY_EMAIL, (email,))

    def update_employee(
        self, employee_id: int, employee_data: dict, company_id: int,
        actor_id: Optional[int] = None,
    ) -> Optional[dict]:
        role = employee_data["role"]
        with db_cursor() as cursor:
            if self._lock_member(cursor, employee_id, company_id) is None:
                return None
            cursor.execute(UPDATE_EMPLOYEE, (
                employee_data["name"],
                employee_data["email"],
                role,
                employee_data["base_salary"],
                company_id if role == "employee" else None,
                employee_id,
            ))
            updated = dict(cursor.fetchone())
            if role == "admin":
                cursor.execute(
                    ASSIGN_ADMIN, (employee_id, company_id, actor_id)
                )
            else:
                cursor.execute(RELEASE_ADMIN, (employee_id,))
            return updated

    def set_employee_active(
        self, employee_id: int, is_active: bool, company_id: int
    ) -> Optional[dict]:
        with db_cursor() as cursor:
            if self._lock_member(cursor, employee_id, company_id) is None:
                return None
            cursor.execute(UPDATE_EMPLOYEE_ACTIVE, (is_active, employee_id))
            return dict(cursor.fetchone())

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
        self, employee_id: int, password_hash: str, company_id: int
    ) -> Optional[dict]:
        with db_cursor() as cursor:
            if self._lock_member(cursor, employee_id, company_id) is None:
                return None
            cursor.execute(RESET_PASSWORD, (password_hash, employee_id))
            return dict(cursor.fetchone())

    def update_password(self, employee_id: int, password_hash: str) -> None:
        with db_cursor() as cursor:
            cursor.execute(UPDATE_PASSWORD, (password_hash, employee_id))

    def list_employees(self, company_id: int) -> list:
        return self._fetch_all(SELECT_EMPLOYEES, (company_id, company_id))

    def create_employee(
        self, employee_data: dict, company_id: Optional[int] = None,
        actor_id: Optional[int] = None,
    ) -> int:
        role = employee_data["role"]
        with db_cursor() as cursor:
            cursor.execute(INSERT_EMPLOYEE, (
                employee_data["name"],
                employee_data["email"],
                role,
                employee_data["base_salary"],
                employee_data["password_hash"],
                company_id if role == "employee" else None,
            ))
            row = cursor.fetchone()
            if not row:
                raise RuntimeError("No se pudo obtener el ID del empleado.")
            employee_id = int(dict(row)["id"])
            if role == "admin" and company_id is not None:
                cursor.execute(
                    ASSIGN_ADMIN, (employee_id, company_id, actor_id)
                )
            return employee_id

    def first_company_id(self) -> Optional[int]:
        row = self._fetch_one(SELECT_FIRST_COMPANY, ())
        return row["id"] if row else None

    def get_receipts_by_employee_id(self, employee_id: int) -> list:
        return self._fetch_all(SELECT_RECEIPTS_BY_EMPLOYEE, (employee_id,))

    def get_receipt_by_period(
        self, employee_id: int, period_start, period_end, company_id: int
    ) -> Optional[dict]:
        return self._fetch_one(
            SELECT_RECEIPT_BY_PERIOD,
            (employee_id, period_start, period_end, company_id),
        )

    def get_receipt_by_id(self, receipt_id: int) -> Optional[dict]:
        return self._fetch_one(SELECT_RECEIPT_BY_ID, (receipt_id,))

    def list_recent_receipts(self, company_id: int, limit: int = 20) -> list:
        return self._fetch_all(SELECT_RECENT_RECEIPTS, (company_id, limit))

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
                    receipt_data["company_id"],
                ),
            )
            row = cursor.fetchone()
            if not row:
                raise ReceiptOfAnotherCompanyError()

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

    def _lock_member(
        self, cursor, employee_id: int, company_id: int
    ) -> Optional[dict]:
        cursor.execute(
            LOCK_MEMBER, (company_id, employee_id, company_id, company_id)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        member = dict(row)
        if member["is_shared"]:
            raise SharedAdminError()
        return member

    def _fetch_one(self, query: str, params: tuple) -> Optional[dict]:
        with db_cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def _fetch_all(self, query: str, params: tuple = ()) -> list:
        with db_cursor() as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def create_password_reset_token(
        self, employee_id: int, token: str, code: str, expires_at
    ) -> None:
        with db_cursor() as cursor:
            cursor.execute(INSERT_PASSWORD_RESET_TOKEN, (employee_id, token, code, expires_at))

    def get_password_reset_token(self, code: str) -> Optional[dict]:
        return self._fetch_one(SELECT_PASSWORD_RESET_TOKEN, (code,))

    def mark_reset_token_used(self, token_id: int) -> None:
        with db_cursor() as cursor:
            cursor.execute(MARK_RESET_TOKEN_USED, (token_id,))


payroll_repository = PayrollRepository()
