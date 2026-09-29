ALTER TABLE employees
    ADD COLUMN IF NOT EXISTS rfc VARCHAR(13),
    ADD COLUMN IF NOT EXISTS curp VARCHAR(18),
    ADD COLUMN IF NOT EXISTS nss VARCHAR(11);

ALTER TABLE employees
    ADD CONSTRAINT employees_rfc_check
        CHECK (rfc ~ '^[A-ZÑ&]{4}[0-9]{6}[A-Z0-9]{2}[0-9A]$'),
    ADD CONSTRAINT employees_curp_check
        CHECK (curp ~ '^[A-Z][AEIOUX][A-Z]{2}[0-9]{6}[HMX][A-Z]{2}[B-DF-HJ-NP-TV-Z]{3}[A-Z0-9][0-9]$'),
    ADD CONSTRAINT employees_nss_check
        CHECK (nss ~ '^[0-9]{11}$');

CREATE UNIQUE INDEX IF NOT EXISTS employees_company_rfc_key
    ON employees (company_id, rfc) WHERE rfc IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS employees_company_curp_key
    ON employees (company_id, curp) WHERE curp IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS employees_company_nss_key
    ON employees (company_id, nss) WHERE nss IS NOT NULL;

CREATE TABLE IF NOT EXISTS salary_history (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE RESTRICT,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    base_salary NUMERIC(12, 2) NOT NULL CHECK (base_salary >= 0),
    valid_from DATE NOT NULL,
    recorded_by INTEGER REFERENCES employees(id) ON DELETE RESTRICT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_salary_history_employee
    ON salary_history (employee_id, company_id, valid_from DESC, id DESC);

INSERT INTO salary_history (employee_id, company_id, base_salary, valid_from)
SELECT e.id, e.company_id, e.base_salary, e.hire_date
  FROM employees e
 WHERE e.role = 'employee' AND e.base_salary IS NOT NULL;

INSERT INTO salary_history (employee_id, company_id, base_salary, valid_from)
SELECT e.id, ca.company_id, e.base_salary, e.hire_date
  FROM employees e
  JOIN company_admins ca ON ca.admin_id = e.id AND ca.is_active
 WHERE e.role = 'admin' AND e.base_salary IS NOT NULL;
