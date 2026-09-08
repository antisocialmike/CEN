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

INSERT INTO employees (name, email, role, base_salary, password_hash)
VALUES (
    'Admin',
    'admin',
    'admin',
    20000.00,
    '$2b$12$y1Iy2U7kAyyl9kbZYBaeGe/Bs0xOMWhiF252PXmYbdfpVZsWGDXpy'
)
ON CONFLICT (email) DO NOTHING;
