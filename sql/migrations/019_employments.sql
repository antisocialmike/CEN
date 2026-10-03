CREATE TABLE IF NOT EXISTS employments (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE RESTRICT,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    hire_date DATE NOT NULL DEFAULT CURRENT_DATE,
    base_salary NUMERIC(12, 2) NOT NULL CHECK (base_salary >= 0),
    tipo_regimen CHAR(2) NOT NULL DEFAULT '02'
        CHECK (tipo_regimen IN ('02', '09')),
    tipo_jornada CHAR(2) NOT NULL DEFAULT '01'
        CHECK (tipo_jornada IN ('01', '02', '03')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deactivated_at TIMESTAMPTZ,
    UNIQUE (employee_id, company_id)
);

CREATE INDEX IF NOT EXISTS idx_employments_company
    ON employments (company_id, is_active DESC);

INSERT INTO employments (employee_id, company_id, hire_date, base_salary,
                         tipo_regimen, tipo_jornada, is_active, created_at,
                         deactivated_at)
SELECT e.id, e.company_id, e.hire_date, e.base_salary, e.tipo_regimen,
       e.tipo_jornada, e.is_active, e.created_at, e.deactivated_at
  FROM employees e
 WHERE e.role = 'employee'
ON CONFLICT (employee_id, company_id) DO NOTHING;

INSERT INTO employments (employee_id, company_id, hire_date, base_salary,
                         tipo_regimen, tipo_jornada, is_active, created_at,
                         deactivated_at)
SELECT e.id, ca.company_id, e.hire_date, e.base_salary, e.tipo_regimen,
       e.tipo_jornada, e.is_active, e.created_at, e.deactivated_at
  FROM employees e
  JOIN company_admins ca ON ca.admin_id = e.id AND ca.is_active
 WHERE e.role = 'admin' AND e.base_salary IS NOT NULL
ON CONFLICT (employee_id, company_id) DO NOTHING;

DROP INDEX IF EXISTS idx_payroll_receipts_employee_range;

CREATE UNIQUE INDEX IF NOT EXISTS idx_payroll_receipts_employment_range
    ON payroll_receipts (employee_id, company_id, period_start, period_end);

ALTER TABLE payroll_receipts
    DROP CONSTRAINT IF EXISTS payroll_receipts_no_overlap;

ALTER TABLE payroll_receipts
    ADD CONSTRAINT payroll_receipts_no_overlap
    EXCLUDE USING gist (
        employee_id WITH =,
        company_id WITH =,
        daterange(period_start, period_end, '[]') WITH &&
    );

ALTER TABLE employees
    DROP COLUMN IF EXISTS company_id,
    DROP COLUMN IF EXISTS base_salary,
    DROP COLUMN IF EXISTS tipo_regimen,
    DROP COLUMN IF EXISTS tipo_jornada,
    DROP COLUMN IF EXISTS hire_date,
    DROP COLUMN IF EXISTS deactivated_at;

CREATE UNIQUE INDEX IF NOT EXISTS employees_rfc_key
    ON employees (rfc) WHERE rfc IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS employees_curp_key
    ON employees (curp) WHERE curp IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS employees_nss_key
    ON employees (nss) WHERE nss IS NOT NULL;
