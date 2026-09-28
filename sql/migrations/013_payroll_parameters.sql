-- Parametros con vigencia del calculo de la nomina (retenciones al trabajador).
--
-- Hasta ahora la UMA, el subsidio para el empleo y la tarifa del ISR vivian
-- fijos en payroll_controller.py, con los valores de 2026: una nomina de 2025
-- se calculaba en silencio con numeros de otro anio. Aqui quedan con su
-- vigencia y su fuente, igual que los del costo patronal (012); la tabla
-- employer_cost_parameters guarda desde ahora los dos tipos de parametro.
--
-- Cobertura: 2025 y 2026. Un periodo sin parametros vigentes no se calcula.

-- --- UMA de 2024 (rige en enero de 2025) y salario minimo de 2025 ---------
INSERT INTO employer_cost_parameters (key, valid_from, valid_to, value, source)
VALUES
    ('uma_diaria', '2024-02-01', '2025-01-31', 108.57,
     'INEGI, comunicado 10/24; DOF 10-01-2024'),
    ('salario_minimo_general', '2025-01-01', '2025-12-31', 278.80,
     'CONASAMI, resolucion publicada en el DOF 19-12-2024')
ON CONFLICT DO NOTHING;

-- --- Subsidio para el empleo ------------------------------------------------
-- El monto mensual es un porcentaje de la UMA mensual (UMA diaria x 30.4). En
-- enero todavia rige la UMA del anio anterior, por eso cada decreto trae un
-- porcentaje de transicion solo para enero.
INSERT INTO employer_cost_parameters (key, valid_from, valid_to, value, source)
VALUES
    ('subsidio_empleo_porcentaje_uma', '2025-01-01', '2025-01-31', 0.1439,
     'Decreto que modifica el que otorga el subsidio para el empleo, DOF '
     '31-12-2024, transitorio: 14.39% de la UMA 2024 en enero de 2025'),
    ('subsidio_empleo_porcentaje_uma', '2025-02-01', '2025-12-31', 0.138,
     'Decreto que modifica el que otorga el subsidio para el empleo, DOF '
     '31-12-2024: 13.8% de la UMA mensual'),
    ('subsidio_empleo_limite_mensual', '2025-01-01', '2025-12-31', 10171.00,
     'Decreto que modifica el que otorga el subsidio para el empleo, DOF '
     '31-12-2024'),
    ('subsidio_empleo_porcentaje_uma', '2026-01-01', '2026-01-31', 0.1559,
     'Decreto que modifica el que otorga el subsidio para el empleo, DOF '
     '31-12-2025, transitorio: 15.59% de la UMA 2025 en enero de 2026'),
    ('subsidio_empleo_porcentaje_uma', '2026-02-01', NULL, 0.1502,
     'Decreto que modifica el que otorga el subsidio para el empleo, DOF '
     '31-12-2025: 15.02% de la UMA mensual'),
    ('subsidio_empleo_limite_mensual', '2026-01-01', NULL, 11492.66,
     'Decreto que modifica el que otorga el subsidio para el empleo, DOF '
     '31-12-2025')
ON CONFLICT DO NOTHING;

-- --- Tarifa mensual del ISR (LISR art. 96) ----------------------------------
-- Un renglon por tramo y por vigencia. upper_limit NULL = "en adelante".
-- Para periodos distintos del mes el calculo la escala por dias (30.4).
-- El primer tramo empieza en 0.00 (el Anexo dice 0.01) para que una base en
-- cero tambien caiga en un renglon.
CREATE TABLE IF NOT EXISTS isr_tariff_brackets (
    id SERIAL PRIMARY KEY,
    valid_from DATE NOT NULL,
    valid_to DATE,
    lower_limit NUMERIC(12, 2) NOT NULL CHECK (lower_limit >= 0),
    upper_limit NUMERIC(12, 2),
    fixed_fee NUMERIC(12, 2) NOT NULL CHECK (fixed_fee >= 0),
    rate NUMERIC(6, 4) NOT NULL CHECK (rate > 0 AND rate < 1),
    source TEXT NOT NULL,
    CHECK (valid_to IS NULL OR valid_to >= valid_from),
    CHECK (upper_limit IS NULL OR upper_limit > lower_limit)
);

CREATE INDEX IF NOT EXISTS idx_isr_tariff_brackets_valid
    ON isr_tariff_brackets (valid_from, valid_to);

INSERT INTO isr_tariff_brackets
    (valid_from, valid_to, lower_limit, upper_limit, fixed_fee, rate, source)
SELECT '2025-01-01', '2025-12-31', t.lower_limit, t.upper_limit, t.fixed_fee,
       t.rate, 'Anexo 8 de la RMF para 2025, apartado V; DOF 30-12-2024'
  FROM (VALUES
      (0.00, 746.04, 0.00, 0.0192),
      (746.05, 6332.05, 14.32, 0.0640),
      (6332.06, 11128.01, 371.83, 0.1088),
      (11128.02, 12935.82, 893.63, 0.1600),
      (12935.83, 15487.71, 1182.88, 0.1792),
      (15487.72, 31236.49, 1640.18, 0.2136),
      (31236.50, 49233.00, 5004.12, 0.2352),
      (49233.01, 93993.90, 9236.89, 0.3000),
      (93993.91, 125325.20, 22665.17, 0.3200),
      (125325.21, 375975.61, 32691.18, 0.3400),
      (375975.62, NULL::NUMERIC, 117912.32, 0.3500)
  ) AS t(lower_limit, upper_limit, fixed_fee, rate)
 WHERE NOT EXISTS (
     SELECT 1 FROM isr_tariff_brackets WHERE valid_from = '2025-01-01'
 );

INSERT INTO isr_tariff_brackets
    (valid_from, valid_to, lower_limit, upper_limit, fixed_fee, rate, source)
SELECT '2026-01-01', NULL, t.lower_limit, t.upper_limit, t.fixed_fee,
       t.rate, 'Anexo 8 de la RMF para 2026, apartado V; DOF 28-12-2025'
  FROM (VALUES
      (0.00, 844.59, 0.00, 0.0192),
      (844.60, 7168.51, 16.22, 0.0640),
      (7168.52, 12598.02, 420.95, 0.1088),
      (12598.03, 14644.64, 1011.68, 0.1600),
      (14644.65, 17533.64, 1339.14, 0.1792),
      (17533.65, 35362.83, 1856.84, 0.2136),
      (35362.84, 55736.68, 5665.16, 0.2352),
      (55736.69, 106410.50, 10457.09, 0.3000),
      (106410.51, 141880.66, 25659.23, 0.3200),
      (141880.67, 425641.99, 37009.69, 0.3400),
      (425642.00, NULL::NUMERIC, 133488.54, 0.3500)
  ) AS t(lower_limit, upper_limit, fixed_fee, rate)
 WHERE NOT EXISTS (
     SELECT 1 FROM isr_tariff_brackets WHERE valid_from = '2026-01-01'
 );
