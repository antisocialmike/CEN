CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    role VARCHAR(30) NOT NULL CHECK (role IN ('admin', 'employee')),
    base_salary NUMERIC(12, 2) NOT NULL CHECK (base_salary >= 0),
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS payroll_receipts (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    gross_salary NUMERIC(12, 2) NOT NULL CHECK (gross_salary >= 0),
    isr_deduction NUMERIC(12, 2) NOT NULL,
    imss_deduction NUMERIC(12, 2) NOT NULL,
    net_salary NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payroll_receipts_employee_created
    ON payroll_receipts (employee_id, created_at DESC);
