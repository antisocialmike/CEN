-- Tipo de nomina y jornada de cada persona (asimilados a salarios).
--
-- Las claves son las de los catalogos del SAT para el CFDI de nomina, para no
-- traducirlas cuando se timbre:
--   c_TipoRegimen  02 Sueldos, 09 Asimilados honorarios
--   c_TipoJornada  01 Diurna (8 h), 02 Nocturna (7 h), 03 Mixta (7.5 h),
--                  las jornadas maximas de la LFT art. 61
-- CEN solo acepta esas por ahora (ver docs/investigacion-tipos-de-nomina.md).
-- Las cuentas que ya existen quedan como sueldos en jornada diurna, que es
-- como se calculaban hasta hoy.

ALTER TABLE employees
    ADD COLUMN IF NOT EXISTS tipo_regimen CHAR(2) NOT NULL DEFAULT '02',
    ADD COLUMN IF NOT EXISTS tipo_jornada CHAR(2) NOT NULL DEFAULT '01';

ALTER TABLE employees
    DROP CONSTRAINT IF EXISTS employees_tipo_regimen_check;

ALTER TABLE employees
    ADD CONSTRAINT employees_tipo_regimen_check
    CHECK (tipo_regimen IN ('02', '09'));

ALTER TABLE employees
    DROP CONSTRAINT IF EXISTS employees_tipo_jornada_check;

ALTER TABLE employees
    ADD CONSTRAINT employees_tipo_jornada_check
    CHECK (tipo_jornada IN ('01', '02', '03'));

-- Foto del regimen con el que se calculo cada recibo: si manana la persona
-- cambia de regimen, sus recibos anteriores siguen diciendo como se pagaron.
ALTER TABLE payroll_receipts
    ADD COLUMN IF NOT EXISTS tipo_regimen CHAR(2) NOT NULL DEFAULT '02';

ALTER TABLE payroll_receipts
    DROP CONSTRAINT IF EXISTS payroll_receipts_tipo_regimen_check;

ALTER TABLE payroll_receipts
    ADD CONSTRAINT payroll_receipts_tipo_regimen_check
    CHECK (tipo_regimen IN ('02', '09'));

-- Si el impuesto sobre nominas del estado grava los honorarios asimilados.
-- Cambia por estado: SLP si (Ley de Hacienda del Estado, art. 20 fr. III);
-- CDMX solo los de consejeros y administradores (Codigo Fiscal, art. 156).
-- NULL = no confirmado: el ISN de un asimilado queda pendiente en su costo.
ALTER TABLE state_payroll_tax_rates
    ADD COLUMN IF NOT EXISTS taxes_assimilated BOOLEAN;
