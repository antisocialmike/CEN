ALTER TABLE employees ADD COLUMN IF NOT EXISTS hire_date DATE;

UPDATE employees SET hire_date = created_at::date WHERE hire_date IS NULL;

ALTER TABLE employees
    ALTER COLUMN hire_date SET DEFAULT CURRENT_DATE,
    ALTER COLUMN hire_date SET NOT NULL;
