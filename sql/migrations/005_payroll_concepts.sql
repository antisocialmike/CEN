ALTER TABLE payroll_receipts
    ADD COLUMN IF NOT EXISTS total_perceptions NUMERIC(12, 2),
    ADD COLUMN IF NOT EXISTS total_deductions NUMERIC(12, 2),
    ADD COLUMN IF NOT EXISTS taxable_base NUMERIC(12, 2);

UPDATE payroll_receipts
   SET total_perceptions = gross_salary,
       total_deductions = isr_deduction + imss_deduction,
       taxable_base = gross_salary
 WHERE total_perceptions IS NULL;

ALTER TABLE payroll_receipts
    ALTER COLUMN total_perceptions SET NOT NULL,
    ALTER COLUMN total_deductions SET NOT NULL,
    ALTER COLUMN taxable_base SET NOT NULL;

CREATE TABLE IF NOT EXISTS payroll_receipt_items (
    id SERIAL PRIMARY KEY,
    receipt_id INTEGER NOT NULL
        REFERENCES payroll_receipts(id) ON DELETE CASCADE,
    kind VARCHAR(12) NOT NULL CHECK (kind IN ('perception', 'deduction')),
    concept VARCHAR(40) NOT NULL,
    description VARCHAR(120) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    taxable NUMERIC(12, 2) NOT NULL DEFAULT 0,
    exempt NUMERIC(12, 2) NOT NULL DEFAULT 0,
    position SMALLINT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_payroll_receipt_items_receipt
    ON payroll_receipt_items (receipt_id, position);

INSERT INTO payroll_receipt_items
    (receipt_id, kind, concept, description, amount, taxable, exempt, position)
SELECT r.id, 'perception', 'sueldo', 'Sueldo del periodo',
       r.gross_salary, r.gross_salary, 0, 0
  FROM payroll_receipts r
 WHERE NOT EXISTS (
     SELECT 1 FROM payroll_receipt_items i
      WHERE i.receipt_id = r.id AND i.concept = 'sueldo'
 );

INSERT INTO payroll_receipt_items
    (receipt_id, kind, concept, description, amount, taxable, exempt, position)
SELECT r.id, 'deduction', 'isr', 'ISR retenido', r.isr_deduction, 0, 0, 1
  FROM payroll_receipts r
 WHERE NOT EXISTS (
     SELECT 1 FROM payroll_receipt_items i
      WHERE i.receipt_id = r.id AND i.concept = 'isr'
 );

INSERT INTO payroll_receipt_items
    (receipt_id, kind, concept, description, amount, taxable, exempt, position)
SELECT r.id, 'deduction', 'imss', 'IMSS retenido', r.imss_deduction, 0, 0, 2
  FROM payroll_receipts r
 WHERE NOT EXISTS (
     SELECT 1 FROM payroll_receipt_items i
      WHERE i.receipt_id = r.id AND i.concept = 'imss'
 );
