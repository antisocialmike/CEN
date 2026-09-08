ALTER TABLE payroll_receipts
    ADD COLUMN IF NOT EXISTS period DATE,
    ADD COLUMN IF NOT EXISTS processed_by VARCHAR(150),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

UPDATE payroll_receipts
   SET period = date_trunc('month', created_at)::date
 WHERE period IS NULL;

UPDATE payroll_receipts
   SET processed_by = 'desconocido'
 WHERE processed_by IS NULL;

DELETE FROM payroll_receipts older
 USING payroll_receipts newer
 WHERE older.employee_id = newer.employee_id
   AND older.period = newer.period
   AND (older.created_at, older.id) < (newer.created_at, newer.id);

ALTER TABLE payroll_receipts
    ALTER COLUMN period SET NOT NULL,
    ALTER COLUMN processed_by SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_payroll_receipts_employee_period
    ON payroll_receipts (employee_id, period);
