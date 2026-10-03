from decimal import Decimal
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

# Una persona pertenece a la empresa si trabaja en ella o si la administra
# con una asignacion activa. Los duenos y el superadmin nunca entran aqui.
MEMBER_FIELDS = (
    "SELECT e.id, e.name, e.email, e.role, m.base_salary, "
    "(e.is_active AND COALESCE(m.is_active, TRUE)) AS is_active, "
    "COALESCE(m.tipo_regimen, '02') AS tipo_regimen, "
    "COALESCE(m.tipo_jornada, '01') AS tipo_jornada, m.hire_date, "
    "e.rfc, e.curp, e.nss "
)
EMPLOYEES_OF_COMPANY = (
    "FROM employees e LEFT JOIN employments m "
    "ON m.employee_id = e.id AND m.company_id = %s "
    "WHERE e.role IN ('admin', 'employee') AND (m.id IS NOT NULL OR EXISTS ("
    "SELECT 1 FROM company_admins ca WHERE ca.admin_id = e.id "
    "AND ca.company_id = %s AND ca.is_active)) "
)
SELECT_EMPLOYEE_BY_ID = MEMBER_FIELDS + EMPLOYEES_OF_COMPANY + "AND e.id = %s;"
SELECT_EMPLOYEE_BY_EMAIL = (
    "SELECT e.id, e.name, e.email, e.role, e.password_hash, e.curp, "
    "e.must_change_password, e.is_active, e.failed_login_attempts, "
    "e.locked_until, e.token_version, "
    "CASE WHEN e.role = 'employee' THEN EXISTS ("
    "SELECT 1 FROM employments m JOIN companies c ON c.id = m.company_id "
    "WHERE m.employee_id = e.id AND m.is_active AND c.is_active) "
    "END AS company_is_active "
    "FROM employees e WHERE e.email = %s;"
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
# Restablecer o cambiar la contrasena sube la version de sesion: los tokens que
# ya se emitieron dejan de valer.
RESET_PASSWORD = (
    "UPDATE employees SET password_hash = %s, must_change_password = TRUE, "
    "failed_login_attempts = 0, locked_until = NULL, "
    "token_version = token_version + 1 WHERE id = %s "
    "RETURNING id, name, email;"
)
SELECT_PASSWORD_HASH = (
    "SELECT password_hash FROM employees WHERE id = %s;"
)
UPDATE_PASSWORD = (
    "UPDATE employees SET password_hash = %s, must_change_password = FALSE, "
    "token_version = token_version + 1 WHERE id = %s;"
)
# El id desempata a los homonimos para que la paginacion no los baraje.
EMPLOYEES_ORDER = "ORDER BY is_active DESC, e.name ASC, e.id ASC"
SELECT_EMPLOYEES = MEMBER_FIELDS + EMPLOYEES_OF_COMPANY + EMPLOYEES_ORDER
SELECT_ALL_EMPLOYEES = SELECT_EMPLOYEES + ";"
SELECT_EMPLOYEES_PAGE = SELECT_EMPLOYEES + " LIMIT %s OFFSET %s;"
COUNT_EMPLOYEES = "SELECT COUNT(*) AS total " + EMPLOYEES_OF_COMPANY + ";"
# Bloquea a la persona mientras se modifica y dice si tambien administra
# otras empresas o trabaja en ellas: en ese caso la cuenta no es solo de esta.
LOCK_MEMBER = (
    "SELECT e.id, e.role, e.name, e.email, e.rfc, e.curp, e.nss, "
    "m.id AS employment_id, m.base_salary, EXISTS ("
    "SELECT 1 FROM company_admins other WHERE other.admin_id = e.id "
    "AND other.company_id <> %s AND other.is_active) AS is_shared, EXISTS ("
    "SELECT 1 FROM employments elsewhere WHERE elsewhere.employee_id = e.id "
    "AND elsewhere.company_id <> %s) AS works_elsewhere "
    "FROM employees e LEFT JOIN employments m "
    "ON m.employee_id = e.id AND m.company_id = %s "
    "WHERE e.id = %s AND e.role IN ('admin', 'employee') "
    "AND (m.id IS NOT NULL OR EXISTS ("
    "SELECT 1 FROM company_admins ca WHERE ca.admin_id = e.id "
    "AND ca.company_id = %s AND ca.is_active)) FOR UPDATE OF e;"
)
LOCK_PERSON_BY_ID = (
    "SELECT id FROM employees WHERE id = %s FOR UPDATE;"
)
UPDATE_IDENTITY = (
    "UPDATE employees SET name = %s, email = %s, role = %s, "
    "rfc = COALESCE(%s, rfc), curp = COALESCE(%s, curp), "
    "nss = COALESCE(%s, nss) WHERE id = %s;"
)
UPSERT_EMPLOYMENT = (
    "INSERT INTO employments (employee_id, company_id, hire_date, "
    "base_salary, tipo_regimen, tipo_jornada) "
    "VALUES (%s, %s, COALESCE(%s, CURRENT_DATE), %s, %s, %s) "
    "ON CONFLICT (employee_id, company_id) DO UPDATE SET "
    "hire_date = COALESCE(%s, employments.hire_date), "
    "base_salary = EXCLUDED.base_salary, "
    "tipo_regimen = EXCLUDED.tipo_regimen, "
    "tipo_jornada = EXCLUDED.tipo_jornada "
    "RETURNING hire_date, (xmax = 0) AS created;"
)
DELETE_EMPLOYMENT = (
    "DELETE FROM employments WHERE employee_id = %s AND company_id = %s;"
)
SELECT_EMPLOYMENT = (
    "SELECT id, is_active FROM employments "
    "WHERE employee_id = %s AND company_id = %s;"
)
ASSIGN_ADMIN = (
    "INSERT INTO company_admins (admin_id, company_id, assigned_by) "
    "VALUES (%s, %s, %s) ON CONFLICT (admin_id, company_id) "
    "DO UPDATE SET is_active = TRUE;"
)
RELEASE_ADMIN = (
    "UPDATE company_admins SET is_active = FALSE WHERE admin_id = %s;"
)
# La fecha de baja solo se toca al cambiar de estado: dar de baja dos veces
# no mueve la primera, y reactivar la borra.
UPDATE_EMPLOYMENT_ACTIVE = (
    "UPDATE employments SET is_active = %s, deactivated_at = CASE "
    "WHEN %s THEN NULL WHEN is_active THEN NOW() ELSE deactivated_at END "
    "WHERE id = %s;"
)
UPDATE_ACCOUNT_ACTIVE = "UPDATE employees SET is_active = %s WHERE id = %s;"
SYNC_ACCOUNT_WITH_EMPLOYMENTS = (
    "UPDATE employees e SET is_active = EXISTS ("
    "SELECT 1 FROM employments m WHERE m.employee_id = e.id AND m.is_active) "
    "WHERE e.id = %s;"
)
INSERT_EMPLOYEE = (
    "INSERT INTO employees (name, email, role, rfc, curp, nss, password_hash, "
    "must_change_password) VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE) "
    "RETURNING id;"
)
INSERT_SALARY_CHANGE = (
    "INSERT INTO salary_history (employee_id, company_id, base_salary, "
    "valid_from, recorded_by) VALUES (%s, %s, %s, COALESCE(%s, CURRENT_DATE), %s);"
)
SELECT_SALARY_HISTORY = (
    "SELECT h.base_salary, h.valid_from, h.recorded_at, "
    "r.name AS recorded_by FROM salary_history h "
    "LEFT JOIN employees r ON r.id = h.recorded_by "
    "WHERE h.employee_id = %s AND h.company_id = %s "
    "ORDER BY h.valid_from DESC, h.id DESC;"
)
SELECT_FIRST_COMPANY = "SELECT id FROM companies ORDER BY id LIMIT 1;"
RECEIPT_ITEMS_JSON = (
    "COALESCE(json_agg(json_build_object("
    "'kind', i.kind, 'concept', i.concept, "
    "'description', i.description, 'amount', i.amount, "
    "'taxable', i.taxable, 'exempt', i.exempt) "
    "ORDER BY i.position) FILTER (WHERE i.id IS NOT NULL), '[]') AS items "
)

# Los recibos de una sola persona, en el mismo orden que el historial de la
# empresa: del periodo mas nuevo al mas viejo, con el id de desempate.
SELECT_EMPLOYEE_RECEIPTS_PAGE = (
    "SELECT r.id, r.employee_id, r.period_start, r.period_end, "  # nosec B608
    "r.gross_salary, r.isr_deduction, "
    "r.imss_deduction, r.net_salary, r.total_perceptions, "
    "r.total_deductions, r.taxable_base, r.periodicity, r.paid_days, "
    "r.tipo_regimen, r.processed_by, r.created_at, "
    "r.updated_at, COALESCE(c.trade_name, c.legal_name) AS company_name, "
    + RECEIPT_ITEMS_JSON
    + "FROM payroll_receipts r JOIN companies c ON c.id = r.company_id "
    "LEFT JOIN payroll_receipt_items i ON i.receipt_id = r.id "
    "WHERE r.employee_id = %s GROUP BY r.id, c.id "
    "ORDER BY r.period_start DESC, r.updated_at DESC, r.id DESC "
    "LIMIT %s OFFSET %s;"
)
COUNT_EMPLOYEE_RECEIPTS = (
    "SELECT COUNT(*) AS total FROM payroll_receipts r "
    "WHERE r.employee_id = %s;"
)
# El id desempata: sin el, dos recibos iguales en periodo y hora podrian
# cambiar de lugar entre una pagina y la siguiente.
SELECT_RECEIPTS_PAGE = (
    "SELECT r.id, r.employee_id, e.name AS employee_name, "  # nosec B608
    "r.period_start, r.period_end, r.periodicity, r.paid_days, "
    "r.gross_salary, r.isr_deduction, r.imss_deduction, r.net_salary, "
    "r.total_perceptions, r.total_deductions, r.taxable_base, "
    "r.tipo_regimen, r.processed_by, r.created_at, r.updated_at, "
    + RECEIPT_ITEMS_JSON
    + "FROM payroll_receipts r JOIN employees e ON e.id = r.employee_id "
    "LEFT JOIN payroll_receipt_items i ON i.receipt_id = r.id "
    "WHERE r.company_id = %s GROUP BY r.id, e.name "
    "ORDER BY r.period_start DESC, r.updated_at DESC, r.id DESC "
    "LIMIT %s OFFSET %s;"
)
COUNT_RECEIPTS = (
    "SELECT COUNT(*) AS total FROM payroll_receipts r WHERE r.company_id = %s;"
)
SELECT_RECEIPT_BY_ID = (
    "SELECT r.id, r.employee_id, e.name AS employee_name, "  # nosec B608
    "e.email AS employee_email, r.company_id, "
    "r.period_start, r.period_end, "
    "r.gross_salary, r.isr_deduction, "
    "r.imss_deduction, r.net_salary, r.total_perceptions, "
    "r.total_deductions, r.taxable_base, r.periodicity, r.paid_days, "
    "r.tipo_regimen, r.processed_by, r.created_at, "
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
    "tipo_regimen, processed_by, company_id) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
    "ON CONFLICT (employee_id, company_id, period_start, period_end) "
    "DO UPDATE SET "
    "periodicity = EXCLUDED.periodicity, "
    "paid_days = EXCLUDED.paid_days, "
    "gross_salary = EXCLUDED.gross_salary, "
    "isr_deduction = EXCLUDED.isr_deduction, "
    "imss_deduction = EXCLUDED.imss_deduction, "
    "net_salary = EXCLUDED.net_salary, "
    "total_perceptions = EXCLUDED.total_perceptions, "
    "total_deductions = EXCLUDED.total_deductions, "
    "taxable_base = EXCLUDED.taxable_base, "
    "tipo_regimen = EXCLUDED.tipo_regimen, "
    "processed_by = EXCLUDED.processed_by, "
    "updated_at = NOW() "
    "RETURNING id, (xmax = 0) AS created;"
)
# Parametros del costo patronal vigentes en una fecha.
SELECT_COST_PARAMETERS = (
    "SELECT key, value FROM employer_cost_parameters "
    "WHERE valid_from <= %s AND (valid_to IS NULL OR valid_to >= %s);"
)
SELECT_CEAV_RATES = (
    "SELECT minimum_wage, upper_uma, rate FROM ceav_employer_rates "
    "WHERE valid_from <= %s AND (valid_to IS NULL OR valid_to >= %s);"
)
SELECT_STATE_PAYROLL_TAX = (
    "SELECT s.rate, s.taxes_assimilated FROM companies c "
    "JOIN state_payroll_tax_rates s ON s.entidad = c.entidad_federativa "
    "WHERE c.id = %s AND s.valid_from <= %s "
    "AND (s.valid_to IS NULL OR s.valid_to >= %s);"
)
SELECT_ISR_BRACKETS = (
    "SELECT lower_limit, upper_limit, fixed_fee, rate FROM isr_tariff_brackets "
    "WHERE valid_from <= %s AND (valid_to IS NULL OR valid_to >= %s) "
    "ORDER BY lower_limit;"
)
SELECT_RISK_PREMIUM = (
    "SELECT rate FROM company_risk_premiums WHERE company_id = %s "
    "AND valid_from <= %s AND (valid_to IS NULL OR valid_to >= %s);"
)
DELETE_EMPLOYER_COST = (
    "DELETE FROM payroll_employer_costs WHERE receipt_id = %s;"
)
INSERT_EMPLOYER_COST = (
    "INSERT INTO payroll_employer_costs (receipt_id, daily_salary, "
    "integration_factor, sbc_daily, uma_daily, days, total, missing) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"
)
INSERT_EMPLOYER_COST_ITEM = (
    "INSERT INTO payroll_employer_cost_items (receipt_id, component, "
    "group_key, description, base, rate, amount, position) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"
)
DELETE_RECEIPT_ITEMS = (
    "DELETE FROM payroll_receipt_items WHERE receipt_id = %s;"
)
INSERT_RECEIPT_ITEM = (
    "INSERT INTO payroll_receipt_items (receipt_id, kind, concept, "
    "description, amount, taxable, exempt, position) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"
)


class SharedAdminError(Exception):
    pass


class SharedPersonError(Exception):
    pass


class AlreadyEmployedError(Exception):
    def __init__(self, is_active: bool):
        super().__init__("La persona ya trabaja en la empresa")
        self.is_active = is_active


IDENTITY_FIELDS = ("name", "email", "role")
FISCAL_FIELDS = ("rfc", "curp", "nss")


def _changes_identity(member: dict, employee_data: dict) -> bool:
    if any(employee_data[f] != member[f] for f in IDENTITY_FIELDS):
        return True
    return any(
        employee_data.get(f) is not None and employee_data.get(f) != member[f]
        for f in FISCAL_FIELDS
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

    def get_employee_by_id(
        self, employee_id: int, company_id: int
    ) -> Optional[dict]:
        return self._fetch_one(
            SELECT_EMPLOYEE_BY_ID, (company_id, company_id, employee_id)
        )

    def get_employee_by_email(self, email: str) -> Optional[dict]:
        return self._fetch_one(SELECT_EMPLOYEE_BY_EMAIL, (email.strip().lower(),))

    def update_employee(
        self, employee_id: int, employee_data: dict, company_id: int,
        actor_id: Optional[int] = None,
    ) -> Optional[dict]:
        role = employee_data["role"]
        with db_cursor() as cursor:
            member = self._lock_member(cursor, employee_id, company_id)
            if member is None:
                return None
            if member["works_elsewhere"] and _changes_identity(
                member, employee_data
            ):
                raise SharedPersonError()
            cursor.execute(UPDATE_IDENTITY, (
                employee_data["name"],
                employee_data["email"],
                role,
                employee_data.get("rfc"),
                employee_data.get("curp"),
                employee_data.get("nss"),
                employee_id,
            ))
            if employee_data["base_salary"] is None:
                cursor.execute(DELETE_EMPLOYMENT, (employee_id, company_id))
            else:
                self._save_employment(
                    cursor, employee_id, company_id, employee_data,
                    member.get("base_salary"), actor_id,
                )
            if role == "admin":
                cursor.execute(
                    ASSIGN_ADMIN, (employee_id, company_id, actor_id)
                )
            else:
                cursor.execute(RELEASE_ADMIN, (employee_id,))
            return self._member_row(cursor, employee_id, company_id)

    def set_employee_active(
        self, employee_id: int, is_active: bool, company_id: int
    ) -> Optional[dict]:
        with db_cursor() as cursor:
            member = self._lock_member(cursor, employee_id, company_id)
            if member is None:
                return None
            if member["employment_id"] is not None:
                cursor.execute(UPDATE_EMPLOYMENT_ACTIVE, (
                    is_active, is_active, member["employment_id"],
                ))
            if is_active or member["role"] == "admin":
                cursor.execute(UPDATE_ACCOUNT_ACTIVE, (is_active, employee_id))
            else:
                cursor.execute(SYNC_ACCOUNT_WITH_EMPLOYMENTS, (employee_id,))
            return self._member_row(cursor, employee_id, company_id)

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
            member = self._lock_member(cursor, employee_id, company_id)
            if member is None:
                return None
            if member["works_elsewhere"]:
                raise SharedPersonError()
            cursor.execute(RESET_PASSWORD, (password_hash, employee_id))
            return dict(cursor.fetchone())

    def update_password(self, employee_id: int, password_hash: str) -> None:
        with db_cursor() as cursor:
            cursor.execute(UPDATE_PASSWORD, (password_hash, employee_id))

    def list_employees(self, company_id: int) -> list:
        return self._fetch_all(SELECT_ALL_EMPLOYEES, (company_id, company_id))

    def page_employees(self, company_id: int, limit: int, offset: int) -> tuple:
        return self._fetch_page(
            SELECT_EMPLOYEES_PAGE, COUNT_EMPLOYEES,
            (company_id, company_id), limit, offset,
        )

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
                employee_data.get("rfc"),
                employee_data.get("curp"),
                employee_data.get("nss"),
                employee_data["password_hash"],
            ))
            row = cursor.fetchone()
            if not row:
                raise RuntimeError("No se pudo obtener el ID del empleado.")
            employee_id = int(dict(row)["id"])
            if role == "admin" and company_id is not None:
                cursor.execute(
                    ASSIGN_ADMIN, (employee_id, company_id, actor_id)
                )
            if company_id is not None and employee_data["base_salary"] is not None:
                self._save_employment(
                    cursor, employee_id, company_id, employee_data, None,
                    actor_id,
                )
            return employee_id

    def hire_existing_employee(
        self, employee_id: int, employment_data: dict, company_id: int,
        actor_id: Optional[int] = None,
    ) -> dict:
        with db_cursor() as cursor:
            cursor.execute(LOCK_PERSON_BY_ID, (employee_id,))
            cursor.execute(SELECT_EMPLOYMENT, (employee_id, company_id))
            current = cursor.fetchone()
            if current is not None:
                raise AlreadyEmployedError(bool(dict(current)["is_active"]))
            self._save_employment(
                cursor, employee_id, company_id, employment_data, None,
                actor_id,
            )
            cursor.execute(UPDATE_ACCOUNT_ACTIVE, (True, employee_id))
            return self._member_row(cursor, employee_id, company_id)

    def _save_employment(
        self, cursor, employee_id: int, company_id: int, data: dict,
        previous_salary, actor_id: Optional[int],
    ) -> None:
        hire_date = data.get("hire_date")
        cursor.execute(UPSERT_EMPLOYMENT, (
            employee_id,
            company_id,
            hire_date,
            data["base_salary"],
            data.get("tipo_regimen", "02"),
            data.get("tipo_jornada", "01"),
            hire_date,
        ))
        saved = dict(cursor.fetchone())
        if saved["created"]:
            valid_from = saved["hire_date"]
        elif previous_salary is not None and Decimal(str(previous_salary)) == Decimal(
            str(data["base_salary"])
        ):
            return
        else:
            valid_from = data.get("salary_valid_from")
        cursor.execute(INSERT_SALARY_CHANGE, (
            employee_id, company_id, data["base_salary"], valid_from, actor_id,
        ))

    def _member_row(self, cursor, employee_id: int, company_id: int) -> dict:
        cursor.execute(
            SELECT_EMPLOYEE_BY_ID, (company_id, company_id, employee_id)
        )
        return dict(cursor.fetchone())

    def salary_history(
        self, employee_id: int, company_id: int
    ) -> Optional[list]:
        with db_cursor() as cursor:
            cursor.execute(
                SELECT_EMPLOYEE_BY_ID, (company_id, company_id, employee_id)
            )
            if cursor.fetchone() is None:
                return None
            cursor.execute(SELECT_SALARY_HISTORY, (employee_id, company_id))
            return [dict(row) for row in cursor.fetchall()]

    def first_company_id(self) -> Optional[int]:
        row = self._fetch_one(SELECT_FIRST_COMPANY, ())
        return row["id"] if row else None

    def page_employee_receipts(
        self, employee_id: int, limit: int, offset: int
    ) -> tuple:
        return self._fetch_page(
            SELECT_EMPLOYEE_RECEIPTS_PAGE, COUNT_EMPLOYEE_RECEIPTS,
            (employee_id,), limit, offset,
        )

    def get_receipt_by_period(
        self, employee_id: int, period_start, period_end, company_id: int
    ) -> Optional[dict]:
        return self._fetch_one(
            SELECT_RECEIPT_BY_PERIOD,
            (employee_id, period_start, period_end, company_id),
        )

    def get_receipt_by_id(self, receipt_id: int) -> Optional[dict]:
        return self._fetch_one(SELECT_RECEIPT_BY_ID, (receipt_id,))

    def page_receipts(self, company_id: int, limit: int, offset: int) -> tuple:
        return self._fetch_page(
            SELECT_RECEIPTS_PAGE, COUNT_RECEIPTS, (company_id,), limit, offset
        )

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
                    receipt_data.get("tipo_regimen", "02"),
                    receipt_data["processed_by"],
                    receipt_data["company_id"],
                ),
            )
            saved = dict(cursor.fetchone())
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

            # El costo patronal se reemplaza junto con el recibo: si se
            # recalcula un periodo, no queda el costo del calculo anterior.
            cursor.execute(DELETE_EMPLOYER_COST, (receipt_id,))
            employer_cost = receipt_data.get("employer_cost")
            if employer_cost is not None:
                self._insert_employer_cost(cursor, receipt_id, employer_cost)

            return {"id": receipt_id, "created": bool(saved["created"])}

    def _insert_employer_cost(
        self, cursor, receipt_id: int, employer_cost: dict
    ) -> None:
        cursor.execute(INSERT_EMPLOYER_COST, (
            receipt_id,
            employer_cost["daily_salary"],
            employer_cost["integration_factor"],
            employer_cost["sbc_daily"],
            employer_cost["uma_daily"],
            employer_cost["days"],
            employer_cost["total"],
            list(employer_cost["missing"]),
        ))
        for item in employer_cost["items"]:
            cursor.execute(INSERT_EMPLOYER_COST_ITEM, (
                receipt_id,
                item["component"],
                item["group_key"],
                item["description"],
                item["base"],
                item["rate"],
                item["amount"],
                item["position"],
            ))

    def employer_cost_parameters(self, company_id: int, on_date) -> dict:
        """Todo lo vigente en `on_date` para calcular el costo patronal."""
        with db_cursor() as cursor:
            cursor.execute(SELECT_COST_PARAMETERS, (on_date, on_date))
            rates = {
                row["key"]: row["value"]
                for row in map(dict, cursor.fetchall())
            }
            cursor.execute(SELECT_CEAV_RATES, (on_date, on_date))
            ceav = [dict(row) for row in cursor.fetchall()]
            cursor.execute(
                SELECT_STATE_PAYROLL_TAX, (company_id, on_date, on_date)
            )
            isn = cursor.fetchone()
            cursor.execute(SELECT_RISK_PREMIUM, (company_id, on_date, on_date))
            risk = cursor.fetchone()
        return {
            "rates": rates,
            "ceav_brackets": ceav,
            "isn_rate": dict(isn)["rate"] if isn else None,
            "isn_taxes_assimilated": (
                dict(isn)["taxes_assimilated"] if isn else None
            ),
            "risk_rate": dict(risk)["rate"] if risk else None,
        }

    def isr_brackets(self, on_date) -> list:
        """La tarifa mensual del ISR vigente en `on_date`, del tramo mas bajo al mas alto."""
        return self._fetch_all(SELECT_ISR_BRACKETS, (on_date, on_date))

    def _lock_member(
        self, cursor, employee_id: int, company_id: int
    ) -> Optional[dict]:
        cursor.execute(LOCK_MEMBER, (
            company_id, company_id, company_id, employee_id, company_id,
        ))
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

    def _fetch_page(
        self, query: str, count_query: str, params: tuple,
        limit: int, offset: int,
    ) -> tuple:
        """Las filas del tramo pedido y el total de la lista completa."""
        with db_cursor() as cursor:
            cursor.execute(count_query, params)
            total = dict(cursor.fetchone())["total"]
            cursor.execute(query, params + (limit, offset))
            return [dict(row) for row in cursor.fetchall()], total


payroll_repository = PayrollRepository()
