ALTER TABLE payroll_receipts RENAME COLUMN period TO period_start;

ALTER TABLE payroll_receipts
    ADD COLUMN IF NOT EXISTS periodicity VARCHAR(12),
    ADD COLUMN IF NOT EXISTS period_end DATE,
    ADD COLUMN IF NOT EXISTS paid_days NUMERIC(5, 2);

UPDATE payroll_receipts
   SET periodicity = 'mensual',
       period_end = (period_start + INTERVAL '1 month - 1 day')::date,
       paid_days = EXTRACT(
           DAY FROM (period_start + INTERVAL '1 month - 1 day')
       )
 WHERE periodicity IS NULL;

ALTER TABLE payroll_receipts
    ALTER COLUMN periodicity SET NOT NULL,
    ALTER COLUMN period_end SET NOT NULL,
    ALTER COLUMN paid_days SET NOT NULL;

ALTER TABLE payroll_receipts
    DROP CONSTRAINT IF EXISTS payroll_receipts_periodicity_check;

ALTER TABLE payroll_receipts
    ADD CONSTRAINT payroll_receipts_periodicity_check
    CHECK (periodicity IN ('mensual', 'quincenal', 'semanal'));

ALTER TABLE payroll_receipts
    DROP CONSTRAINT IF EXISTS payroll_receipts_period_order_check;

ALTER TABLE payroll_receipts
    ADD CONSTRAINT payroll_receipts_period_order_check
    CHECK (period_end >= period_start);

DROP INDEX IF EXISTS idx_payroll_receipts_employee_period;

CREATE UNIQUE INDEX IF NOT EXISTS idx_payroll_receipts_employee_range
    ON payroll_receipts (employee_id, period_start, period_end);

CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE payroll_receipts
    DROP CONSTRAINT IF EXISTS payroll_receipts_no_overlap;

ALTER TABLE payroll_receipts
    ADD CONSTRAINT payroll_receipts_no_overlap
    EXCLUDE USING gist (
        employee_id WITH =,
        daterange(period_start, period_end, '[]') WITH &&
    );
