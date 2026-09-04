CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    role VARCHAR(30) NOT NULL,
    base_salary NUMERIC(12, 2) NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS payroll_receipts (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    gross_salary NUMERIC(12, 2) NOT NULL,
    isr_deduction NUMERIC(12, 2) NOT NULL,
    imss_deduction NUMERIC(12, 2) NOT NULL,
    net_salary NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
