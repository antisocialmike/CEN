CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    legal_name VARCHAR(200) NOT NULL,
    trade_name VARCHAR(150),
    rfc VARCHAR(13) UNIQUE
        CHECK (rfc ~ '^[A-ZÑ&]{3,4}[0-9]{6}[A-Z0-9]{3}$'),
    registro_patronal VARCHAR(11)
        CHECK (registro_patronal ~ '^[A-Z][0-9]{10}$'),
    entidad_federativa CHAR(3) CHECK (entidad_federativa IN (
        'AGU', 'BCN', 'BCS', 'CAM', 'CHP', 'CHH', 'CMX', 'COA',
        'COL', 'DUR', 'GUA', 'GRO', 'HID', 'JAL', 'MEX', 'MIC',
        'MOR', 'NAY', 'NLE', 'OAX', 'PUE', 'QUE', 'ROO', 'SLP',
        'SIN', 'SON', 'TAB', 'TAM', 'TLA', 'VER', 'YUC', 'ZAC'
    )),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO companies (legal_name)
SELECT 'Empresa principal'
 WHERE NOT EXISTS (SELECT 1 FROM companies);

CREATE TABLE IF NOT EXISTS company_owners (
    owner_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE RESTRICT,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (owner_id, company_id)
);

CREATE INDEX IF NOT EXISTS idx_company_owners_company
    ON company_owners (company_id);

CREATE TABLE IF NOT EXISTS company_admins (
    admin_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE RESTRICT,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    assigned_by INTEGER REFERENCES employees(id) ON DELETE RESTRICT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (admin_id, company_id)
);

CREATE INDEX IF NOT EXISTS idx_company_admins_company
    ON company_admins (company_id);

ALTER TABLE employees
    DROP CONSTRAINT IF EXISTS employees_role_check;

ALTER TABLE employees
    ADD CONSTRAINT employees_role_check
    CHECK (role IN ('superadmin', 'owner', 'admin', 'employee'));

ALTER TABLE employees
    ADD COLUMN IF NOT EXISTS company_id INTEGER
        REFERENCES companies(id) ON DELETE RESTRICT;

UPDATE employees
   SET company_id = (SELECT id FROM companies ORDER BY id LIMIT 1)
 WHERE role = 'employee' AND company_id IS NULL;

INSERT INTO company_admins (admin_id, company_id)
SELECT e.id, (SELECT id FROM companies ORDER BY id LIMIT 1)
  FROM employees e
 WHERE e.role = 'admin'
ON CONFLICT (admin_id, company_id) DO NOTHING;

ALTER TABLE employees
    DROP CONSTRAINT IF EXISTS employees_company_by_role_check;

ALTER TABLE employees
    ADD CONSTRAINT employees_company_by_role_check
    CHECK ((role = 'employee') = (company_id IS NOT NULL));

ALTER TABLE employees
    ALTER COLUMN base_salary DROP NOT NULL;

ALTER TABLE employees
    DROP CONSTRAINT IF EXISTS employees_salary_by_role_check;

ALTER TABLE employees
    ADD CONSTRAINT employees_salary_by_role_check
    CHECK (role <> 'employee' OR base_salary IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_employees_company
    ON employees (company_id, is_active DESC, name ASC);

ALTER TABLE payroll_receipts
    ADD COLUMN IF NOT EXISTS company_id INTEGER
        REFERENCES companies(id) ON DELETE RESTRICT;

UPDATE payroll_receipts r
   SET company_id = COALESCE(
       (SELECT e.company_id FROM employees e WHERE e.id = r.employee_id),
       (SELECT id FROM companies ORDER BY id LIMIT 1)
   )
 WHERE r.company_id IS NULL;

ALTER TABLE payroll_receipts
    ALTER COLUMN company_id SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_payroll_receipts_company_period
    ON payroll_receipts (company_id, period_start);
