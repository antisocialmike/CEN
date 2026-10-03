from datetime import date
from typing import Optional

from ..config.database import db_cursor

# Todas las consultas de un tablero leen la misma foto de la base: sin esto,
# un recibo guardado a media consulta podria aparecer en la serie mensual y
# no en los totales.
CONSISTENT_SNAPSHOT = (
    "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY;"
)

# Los filtros de recibos se repiten literales en cada consulta, en el mismo
# orden de parametros: empresas, desde, hasta, periodicidad, periodicidad.
PAYROLL_TOTALS = (
    "SELECT COALESCE(SUM(r.total_perceptions), 0) AS gross_payroll, "
    "COALESCE(SUM(r.net_salary), 0) AS net_paid, "
    "COALESCE(SUM(r.isr_deduction), 0) AS isr_withheld, "
    "COALESCE(SUM(r.imss_deduction), 0) AS imss_withheld, "
    "COALESCE(SUM(r.total_deductions), 0) AS total_deductions, "
    "COUNT(*) AS receipts, "
    "COUNT(DISTINCT r.employee_id) AS paid_employees "
    "FROM payroll_receipts r "
    "WHERE r.company_id = ANY(%s) AND r.period_start BETWEEN %s AND %s "
    "AND (%s::text IS NULL OR r.periodicity = %s);"
)
MONTHLY_PAYROLL = (
    "SELECT m.month::date AS month, "
    "COALESCE(SUM(r.total_perceptions), 0) AS gross_payroll, "
    "COALESCE(SUM(r.net_salary), 0) AS net_paid, "
    "COALESCE(SUM(r.isr_deduction), 0) AS isr_withheld, "
    "COALESCE(SUM(r.imss_deduction), 0) AS imss_withheld, "
    "COALESCE(SUM(r.total_deductions), 0) AS total_deductions, "
    "COUNT(r.id) AS receipts "
    "FROM generate_series(date_trunc('month', %s::date), "
    "date_trunc('month', %s::date), interval '1 month') AS m(month) "
    "LEFT JOIN payroll_receipts r "
    "ON date_trunc('month', r.period_start) = m.month "
    "AND r.company_id = ANY(%s) AND r.period_start BETWEEN %s AND %s "
    "AND (%s::text IS NULL OR r.periodicity = %s) "
    "GROUP BY m.month ORDER BY m.month;"
)
CONCEPTS = (
    "SELECT i.kind, CASE WHEN i.concept = 'sueldo' AND r.tipo_regimen = '09' "
    "THEN 'honorarios' ELSE i.concept END AS concept, "
    "MIN(i.description) AS description, "
    "SUM(i.amount) AS amount, SUM(i.taxable) AS taxable, "
    "SUM(i.exempt) AS exempt "
    "FROM payroll_receipt_items i "
    "JOIN payroll_receipts r ON r.id = i.receipt_id "
    "WHERE r.company_id = ANY(%s) AND r.period_start BETWEEN %s AND %s "
    "AND (%s::text IS NULL OR r.periodicity = %s) "
    "GROUP BY 1, 2 ORDER BY i.kind DESC, SUM(i.amount) DESC;"
)
HEADCOUNT_NOW = (
    "SELECT COUNT(*) FILTER (WHERE em.is_active) AS active, "
    "COUNT(*) FILTER (WHERE NOT em.is_active) AS inactive "
    "FROM employments em JOIN employees e ON e.id = em.employee_id "
    "WHERE em.company_id = ANY(%s) AND e.role = 'employee';"
)
HEADCOUNT_BY_MONTH = (
    "SELECT m.month::date AS month, "
    "COUNT(em.id) FILTER (WHERE date_trunc('month', em.created_at) = m.month) "
    "AS hires, "
    "COUNT(em.id) FILTER ("
    "WHERE date_trunc('month', em.deactivated_at) = m.month) AS terminations "
    "FROM generate_series(date_trunc('month', %s::date), "
    "date_trunc('month', %s::date), interval '1 month') AS m(month) "
    "LEFT JOIN (employments em JOIN employees e ON e.id = em.employee_id "
    "AND e.role = 'employee') ON em.company_id = ANY(%s) "
    "AND (date_trunc('month', em.created_at) = m.month "
    "OR date_trunc('month', em.deactivated_at) = m.month) "
    "GROUP BY m.month ORDER BY m.month;"
)
TOP_SALARIES = (
    "SELECT e.id, e.name, c.legal_name AS company_name, em.base_salary "
    "FROM employments em JOIN employees e ON e.id = em.employee_id "
    "JOIN companies c ON c.id = em.company_id "
    "WHERE em.company_id = ANY(%s) AND e.role = 'employee' AND em.is_active "
    "ORDER BY em.base_salary DESC, e.name ASC LIMIT 5;"
)
SALARY_HISTOGRAM = (
    "SELECT b.label, b.min_salary, b.max_salary, "
    "COUNT(em.id) AS employees "
    "FROM (VALUES "
    "(1, 'Hasta 10,000', 0, 10000), "
    "(2, '10,000 a 20,000', 10000, 20000), "
    "(3, '20,000 a 35,000', 20000, 35000), "
    "(4, '35,000 a 50,000', 35000, 50000), "
    "(5, '50,000 a 80,000', 50000, 80000), "
    "(6, 'Más de 80,000', 80000, NULL)"
    ") AS b(position, label, min_salary, max_salary) "
    "LEFT JOIN (employments em JOIN employees e ON e.id = em.employee_id "
    "AND e.role = 'employee') ON em.company_id = ANY(%s) AND em.is_active "
    "AND em.base_salary >= b.min_salary "
    "AND (b.max_salary IS NULL OR em.base_salary < b.max_salary) "
    "GROUP BY b.position, b.label, b.min_salary, b.max_salary "
    "ORDER BY b.position;"
)
# El costo patronal es uno por recibo (receipt_id es su llave): unirlo no
# repite recibos. Los que no lo tienen calculado suman cero, como en los KPI.
COMPANY_COMPARISON = (
    "SELECT c.id, c.legal_name, c.is_active, "
    "COALESCE(SUM(r.total_perceptions), 0) AS gross_payroll, "
    "COALESCE(SUM(r.net_salary), 0) AS net_paid, "
    "COALESCE(SUM(ec.total), 0) AS employer_cost, "
    "COALESCE(SUM(r.total_perceptions), 0) + COALESCE(SUM(ec.total), 0) "
    "AS total_cost, "
    "COUNT(r.id) AS receipts, "
    "COUNT(DISTINCT r.employee_id) AS paid_employees, "
    "(SELECT COUNT(*) FROM employments em JOIN employees e "
    "ON e.id = em.employee_id WHERE em.company_id = c.id "
    "AND e.role = 'employee' AND em.is_active) AS active_employees "
    "FROM companies c "
    "LEFT JOIN payroll_receipts r ON r.company_id = c.id "
    "AND r.period_start BETWEEN %s AND %s "
    "AND (%s::text IS NULL OR r.periodicity = %s) "
    "LEFT JOIN payroll_employer_costs ec ON ec.receipt_id = r.id "
    "WHERE c.id = ANY(%s) "
    "GROUP BY c.id ORDER BY gross_payroll DESC, c.legal_name ASC;"
)
# Costo patronal. covered_gross es la nomina de los recibos que si tienen
# costo calculado: el porcentaje se saca solo sobre esos, para no diluirlo
# con recibos emitidos antes de que existiera el calculo.
EMPLOYER_TOTALS = (
    "SELECT COALESCE(SUM(ec.total), 0) AS employer_cost, "
    "COALESCE(SUM(r.total_perceptions) "
    "FILTER (WHERE ec.receipt_id IS NOT NULL), 0) AS covered_gross, "
    "COUNT(ec.receipt_id) AS receipts_with_cost, "
    "COUNT(ec.receipt_id) FILTER (WHERE cardinality(ec.missing) > 0) "
    "AS receipts_incomplete, "
    "COUNT(*) - COUNT(ec.receipt_id) AS receipts_without_cost "
    "FROM payroll_receipts r "
    "LEFT JOIN payroll_employer_costs ec ON ec.receipt_id = r.id "
    "WHERE r.company_id = ANY(%s) AND r.period_start BETWEEN %s AND %s "
    "AND (%s::text IS NULL OR r.periodicity = %s);"
)
EMPLOYER_BY_COMPONENT = (
    "SELECT i.group_key, i.component, MIN(i.description) AS description, "
    "SUM(i.amount) AS amount "
    "FROM payroll_employer_cost_items i "
    "JOIN payroll_receipts r ON r.id = i.receipt_id "
    "WHERE r.company_id = ANY(%s) AND r.period_start BETWEEN %s AND %s "
    "AND (%s::text IS NULL OR r.periodicity = %s) "
    "GROUP BY i.group_key, i.component ORDER BY SUM(i.amount) DESC;"
)
EMPLOYER_MISSING = (
    "SELECT m.name, COUNT(*) AS receipts "
    "FROM payroll_receipts r "
    "JOIN payroll_employer_costs ec ON ec.receipt_id = r.id "
    "CROSS JOIN LATERAL unnest(ec.missing) AS m(name) "
    "WHERE r.company_id = ANY(%s) AND r.period_start BETWEEN %s AND %s "
    "AND (%s::text IS NULL OR r.periodicity = %s) "
    "GROUP BY m.name ORDER BY m.name;"
)
# Las partidas se suman por recibo antes de unirlas con los meses: unirlas
# directo multiplicaria la nomina de cada recibo por su numero de partidas.
EMPLOYER_MONTHLY = (
    "SELECT m.month::date AS month, "
    "COALESCE(SUM(x.imss), 0) AS imss, COALESCE(SUM(x.sar), 0) AS sar, "
    "COALESCE(SUM(x.infonavit), 0) AS infonavit, "
    "COALESCE(SUM(x.isn), 0) AS isn, "
    "COALESCE(SUM(r.total_perceptions) "
    "FILTER (WHERE x.receipt_id IS NOT NULL), 0) AS covered_gross "
    "FROM generate_series(date_trunc('month', %s::date), "
    "date_trunc('month', %s::date), interval '1 month') AS m(month) "
    "LEFT JOIN payroll_receipts r "
    "ON date_trunc('month', r.period_start) = m.month "
    "AND r.company_id = ANY(%s) AND r.period_start BETWEEN %s AND %s "
    "AND (%s::text IS NULL OR r.periodicity = %s) "
    "LEFT JOIN ("
    "SELECT receipt_id, "
    "SUM(amount) FILTER (WHERE group_key = 'imss') AS imss, "
    "SUM(amount) FILTER (WHERE group_key = 'sar') AS sar, "
    "SUM(amount) FILTER (WHERE group_key = 'infonavit') AS infonavit, "
    "SUM(amount) FILTER (WHERE group_key = 'isn') AS isn "
    "FROM payroll_employer_cost_items GROUP BY receipt_id"
    ") AS x ON x.receipt_id = r.id "
    "GROUP BY m.month ORDER BY m.month;"
)
# El resumen de una persona: lo que cobro en el ano y sus ultimos periodos.
EMPLOYEE_YEAR_TOTALS = (
    "SELECT COALESCE(SUM(r.total_perceptions), 0) AS gross_payroll, "
    "COALESCE(SUM(r.isr_deduction), 0) AS isr_withheld, "
    "COALESCE(SUM(r.imss_deduction), 0) AS imss_withheld, "
    "COALESCE(SUM(r.net_salary), 0) AS net_paid, "
    "COUNT(*) AS receipts "
    "FROM payroll_receipts r "
    "WHERE r.employee_id = %s AND r.period_start >= %s "
    "AND r.period_start < %s;"
)
EMPLOYEE_RECENT_RECEIPTS = (
    "SELECT r.id, r.period_start, r.period_end, r.periodicity, "
    "r.net_salary, r.total_perceptions, "
    "COALESCE(c.trade_name, c.legal_name) AS company_name "
    "FROM payroll_receipts r JOIN companies c ON c.id = r.company_id "
    "WHERE r.employee_id = %s "
    "ORDER BY r.period_start DESC, r.updated_at DESC, r.id DESC LIMIT %s;"
)
EMPLOYEE_RECENT_PERIODS = 12
# El resumen del admin. Las personas son las mismas que ve en "Usuarios" y en
# la calculadora: los de la empresa y sus admins con asignacion activa. En la
# nomina esta quien sigue activo y tiene salario.
ON_PAYROLL = (
    "FROM employments em JOIN employees e ON e.id = em.employee_id "
    "WHERE em.company_id = %s AND em.is_active AND e.is_active "
    "AND e.role IN ('admin', 'employee') "
)
# COUNT(*) OVER () da el total antes del LIMIT: la lista se recorta, la cifra no.
ADMIN_PENDING = (
    "SELECT e.id, e.name, em.tipo_regimen, COUNT(*) OVER () AS total "  # nosec B608
    + ON_PAYROLL
    + "AND NOT EXISTS (SELECT 1 FROM payroll_receipts r "  # nosec B608
    "WHERE r.employee_id = e.id AND r.company_id = %s "
    "AND r.period_start >= %s AND r.period_start < %s) "
    "ORDER BY e.name ASC, e.id ASC LIMIT %s;"
)
ADMIN_REGIMES = (
    "SELECT em.tipo_regimen, COUNT(*) AS people "
    + ON_PAYROLL
    + "GROUP BY em.tipo_regimen ORDER BY em.tipo_regimen;"
)
ADMIN_LAST_MONTH = (
    "WITH latest AS (SELECT date_trunc('month', MAX(period_start)) AS month "
    "FROM payroll_receipts WHERE company_id = %s) "
    "SELECT latest.month::date AS month, "
    "COALESCE(SUM(r.total_perceptions), 0) AS gross_payroll, "
    "COALESCE(SUM(r.net_salary), 0) AS net_paid, "
    "COALESCE(SUM(r.isr_deduction), 0) AS isr_withheld, "
    "COALESCE(SUM(r.imss_deduction), 0) AS imss_withheld, "
    "COUNT(r.id) AS receipts, "
    "COUNT(DISTINCT r.employee_id) AS paid_people "
    "FROM latest LEFT JOIN payroll_receipts r ON r.company_id = %s "
    "AND date_trunc('month', r.period_start) = latest.month "
    "GROUP BY latest.month;"
)
ADMIN_MOVEMENTS = (
    "SELECT e.id, e.name, 'alta' AS kind, em.created_at AS happened_at "
    "FROM employments em JOIN employees e ON e.id = em.employee_id "
    "WHERE em.company_id = %s "
    "UNION ALL "
    "SELECT e.id, e.name, 'baja' AS kind, em.deactivated_at AS happened_at "
    "FROM employments em JOIN employees e ON e.id = em.employee_id "
    "WHERE em.company_id = %s AND em.deactivated_at IS NOT NULL "
    "ORDER BY happened_at DESC, id DESC LIMIT %s;"
)
ADMIN_PENDING_SHOWN = 8
# El tablero del superadmin: solo conteos de la plataforma. Ninguna consulta
# toca los recibos: el superadmin no ve la nomina de las empresas.
PLATFORM_COMPANIES = (
    "SELECT COUNT(*) FILTER (WHERE c.is_active) AS active, "
    "COUNT(*) FILTER (WHERE NOT c.is_active) AS inactive "
    "FROM companies c;"
)
PLATFORM_USERS = (
    "SELECT e.role, COUNT(*) FILTER (WHERE e.is_active) AS active, "
    "COUNT(*) FILTER (WHERE NOT e.is_active) AS inactive "
    "FROM employees e WHERE e.role IN ('owner', 'admin', 'employee') "
    "GROUP BY e.role;"
)
# Sin dueno activo: la regla del 409 lo impide para las empresas activas, pero
# quedan las que nacieron antes de ella (la "Empresa principal" de la 009).
PLATFORM_ORPHANED = (
    "SELECT c.id, c.legal_name, c.is_active, COUNT(*) OVER () AS total "
    "FROM companies c WHERE NOT EXISTS ("
    "SELECT 1 FROM company_owners co JOIN employees o ON o.id = co.owner_id "
    "WHERE co.company_id = c.id AND o.is_active) "
    "ORDER BY c.is_active DESC, c.legal_name ASC, c.id ASC LIMIT %s;"
)
PLATFORM_SIGNUPS = (
    "SELECT m.month::date AS month, "
    "(SELECT COUNT(*) FROM companies c "
    "WHERE date_trunc('month', c.created_at) = m.month) AS companies, "
    "(SELECT COUNT(*) FROM employees e WHERE e.role = 'owner' "
    "AND date_trunc('month', e.created_at) = m.month) AS owners "
    "FROM generate_series(date_trunc('month', %s::date), "
    "date_trunc('month', %s::date), interval '1 month') AS m(month) "
    "ORDER BY m.month;"
)
# El objetivo es un dueno o una empresa segun target_type; el nombre sale de
# la tabla que toca.
PLATFORM_ACTIVITY = (
    "SELECT l.id, l.action, l.target_type, l.created_at, "
    "a.name AS actor_name, COALESCE(o.name, c.legal_name) AS target_name "
    "FROM platform_audit_log l JOIN employees a ON a.id = l.actor_id "
    "LEFT JOIN employees o ON l.target_type = 'owner' AND o.id = l.target_id "
    "LEFT JOIN companies c ON l.target_type = 'company' "
    "AND c.id = l.target_id "
    "ORDER BY l.created_at DESC, l.id DESC LIMIT %s;"
)
PLATFORM_ORPHANED_SHOWN = 5
PLATFORM_ACTIVITY_SHOWN = 10
ADMIN_MOVEMENTS_SHOWN = 5
SELECT_OWNER_COMPANY_IDS = (
    "SELECT company_id FROM company_owners WHERE owner_id = %s "
    "ORDER BY company_id;"
)


class AnalyticsRepository:
    def owner_company_ids(self, owner_id: int) -> list:
        with db_cursor() as cursor:
            cursor.execute(SELECT_OWNER_COMPANY_IDS, (owner_id,))
            return [dict(row)["company_id"] for row in cursor.fetchall()]

    def payroll_analytics(
        self,
        company_ids: list,
        start: date,
        end: date,
        previous_start: date,
        previous_end: date,
        periodicity: Optional[str],
        compare_companies: bool,
    ) -> dict:
        receipts = (company_ids, start, end, periodicity, periodicity)
        previous = (
            company_ids, previous_start, previous_end, periodicity, periodicity
        )
        with db_cursor() as cursor:
            cursor.execute(CONSISTENT_SNAPSHOT)

            def one(query: str, params: tuple) -> dict:
                cursor.execute(query, params)
                return dict(cursor.fetchone())

            def many(query: str, params: tuple) -> list:
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]

            return {
                "totals": one(PAYROLL_TOTALS, receipts),
                "previous_totals": one(PAYROLL_TOTALS, previous),
                "monthly": many(MONTHLY_PAYROLL, (start, end) + receipts),
                "concepts": many(CONCEPTS, receipts),
                "headcount": one(HEADCOUNT_NOW, (company_ids,)),
                "headcount_by_month": many(
                    HEADCOUNT_BY_MONTH, (start, end, company_ids)
                ),
                "top_salaries": many(TOP_SALARIES, (company_ids,)),
                "salary_histogram": many(SALARY_HISTOGRAM, (company_ids,)),
                "companies": many(COMPANY_COMPARISON, (
                    start, end, periodicity, periodicity, company_ids,
                )) if compare_companies else [],
                "employer": one(EMPLOYER_TOTALS, receipts),
                "previous_employer": one(EMPLOYER_TOTALS, previous),
                "employer_components": many(EMPLOYER_BY_COMPONENT, receipts),
                "employer_missing": many(EMPLOYER_MISSING, receipts),
                "employer_monthly": many(
                    EMPLOYER_MONTHLY, (start, end) + receipts
                ),
            }

    def employee_summary(
        self, employee_id: int, year_start: date, next_year_start: date
    ) -> dict:
        with db_cursor() as cursor:
            cursor.execute(CONSISTENT_SNAPSHOT)
            cursor.execute(
                EMPLOYEE_YEAR_TOTALS,
                (employee_id, year_start, next_year_start),
            )
            year_totals = dict(cursor.fetchone())
            cursor.execute(
                EMPLOYEE_RECENT_RECEIPTS,
                (employee_id, EMPLOYEE_RECENT_PERIODS),
            )
            recent = [dict(row) for row in cursor.fetchall()]
        return {"year_totals": year_totals, "recent": recent}

    def admin_summary(
        self, company_id: int, month_start: date, next_month_start: date
    ) -> dict:
        company = (company_id,)
        with db_cursor() as cursor:
            cursor.execute(CONSISTENT_SNAPSHOT)

            def many(query: str, params: tuple) -> list:
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]

            cursor.execute(ADMIN_LAST_MONTH, (company_id, company_id))
            last_month = cursor.fetchone()
            return {
                "pending": many(ADMIN_PENDING, company + (
                    company_id, month_start, next_month_start,
                    ADMIN_PENDING_SHOWN,
                )),
                "regimes": many(ADMIN_REGIMES, company),
                "last_month": dict(last_month) if last_month else None,
                "movements": many(
                    ADMIN_MOVEMENTS, company + company + (ADMIN_MOVEMENTS_SHOWN,)
                ),
            }

    def platform_summary(self, start: date, end: date) -> dict:
        with db_cursor() as cursor:
            cursor.execute(CONSISTENT_SNAPSHOT)

            def many(query: str, params: tuple) -> list:
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]

            cursor.execute(PLATFORM_COMPANIES, ())
            companies = dict(cursor.fetchone())
            return {
                "companies": companies,
                "users": many(PLATFORM_USERS, ()),
                "orphaned": many(
                    PLATFORM_ORPHANED, (PLATFORM_ORPHANED_SHOWN,)
                ),
                "signups": many(PLATFORM_SIGNUPS, (start, end)),
                "activity": many(
                    PLATFORM_ACTIVITY, (PLATFORM_ACTIVITY_SHOWN,)
                ),
            }


analytics_repository = AnalyticsRepository()
