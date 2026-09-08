ALTER TABLE employees
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE payroll_receipts
    DROP CONSTRAINT IF EXISTS payroll_receipts_employee_id_fkey;

ALTER TABLE payroll_receipts
    ADD CONSTRAINT payroll_receipts_employee_id_fkey
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE RESTRICT;

CREATE INDEX IF NOT EXISTS idx_employees_active_name
    ON employees (is_active DESC, name ASC);
