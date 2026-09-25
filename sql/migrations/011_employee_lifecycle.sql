ALTER TABLE employees
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS deactivated_at TIMESTAMPTZ;

-- Las cuentas anteriores a esta migracion no guardaban su alta: se toma el
-- primer periodo que cobraron, que es lo mas cercano que queda registrado.
-- Las bajas anteriores no se pueden fechar y se quedan sin deactivated_at.
UPDATE employees e
   SET created_at = first_receipt.period_start
  FROM (
      SELECT employee_id, MIN(period_start)::timestamptz AS period_start
        FROM payroll_receipts
       GROUP BY employee_id
  ) AS first_receipt
 WHERE first_receipt.employee_id = e.id
   AND first_receipt.period_start < e.created_at;

CREATE INDEX IF NOT EXISTS idx_employees_company_created
    ON employees (company_id, created_at);

CREATE INDEX IF NOT EXISTS idx_employees_company_deactivated
    ON employees (company_id, deactivated_at)
    WHERE deactivated_at IS NOT NULL;
