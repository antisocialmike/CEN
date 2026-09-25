-- Costo patronal: parametros con vigencia y el costo calculado de cada recibo.
--
-- Ninguna tasa vive en el codigo. Cada valor lleva su fuente; los que no se
-- pudieron confirmar en una fuente oficial NO se siembran: el calculo marca
-- ese componente como pendiente en lugar de inventarlo.

-- --- Parametros escalares (UMA, salario minimo, tasas por ramo) ------------
CREATE TABLE IF NOT EXISTS employer_cost_parameters (
    id SERIAL PRIMARY KEY,
    key VARCHAR(60) NOT NULL,
    valid_from DATE NOT NULL,
    valid_to DATE,
    value NUMERIC(14, 6) NOT NULL CHECK (value >= 0),
    source TEXT NOT NULL,
    CHECK (valid_to IS NULL OR valid_to >= valid_from),
    EXCLUDE USING gist (
        key WITH =,
        daterange(valid_from, valid_to, '[]') WITH &&
    )
);

INSERT INTO employer_cost_parameters (key, valid_from, valid_to, value, source)
VALUES
    ('uma_diaria', '2025-02-01', '2026-01-31', 113.14,
     'INEGI, comunicado 1/25; DOF 10-01-2025'),
    ('uma_diaria', '2026-02-01', NULL, 117.31,
     'INEGI, comunicado de la UMA 2026; DOF 09-01-2026'),
    ('salario_minimo_general', '2026-01-01', NULL, 315.04,
     'CONASAMI, resolucion publicada en el DOF 09-12-2025'),
    -- Desde la desindexacion (DOF 27-01-2016) las referencias de la LSS al
    -- salario minimo como unidad de medida se leen en UMA.
    ('imss_em_cuota_fija', '2016-01-28', NULL, 0.204,
     'LSS art. 106 fr. I y transitorio decimonoveno: 13.9% + 0.65 x 10 anios'),
    ('imss_em_excedente', '2016-01-28', NULL, 0.011,
     'LSS art. 106 fr. II y transitorio decimonoveno: 6% - 0.49 x 10 anios'),
    ('imss_em_excedente_umbral_uma', '2016-01-28', NULL, 3,
     'LSS art. 106 fr. II: excedente de tres veces la UMA'),
    ('imss_em_prestaciones_dinero', '2016-01-28', NULL, 0.007,
     'LSS art. 107: 70% de una cuota del 1% del SBC'),
    ('imss_gastos_medicos_pensionados', '2016-01-28', NULL, 0.0105,
     'LSS art. 25: 1.05% del SBC a cargo del patron'),
    ('imss_invalidez_vida', '2016-01-28', NULL, 0.0175,
     'LSS art. 147: 1.75% del SBC'),
    ('imss_guarderias', '2016-01-28', NULL, 0.01,
     'LSS art. 211: 1% del SBC'),
    ('imss_retiro', '2016-01-28', NULL, 0.02,
     'LSS art. 168 fr. I: 2% del SBC'),
    ('imss_tope_uma', '2016-01-28', NULL, 25,
     'LSS art. 28: limite superior de 25 veces (UMA desde DOF 27-01-2016)'),
    ('infonavit', '2016-01-28', NULL, 0.05,
     'Ley del INFONAVIT art. 29 fr. II: 5% con la base y el tope de la LSS'),
    ('lft_aguinaldo_dias', '1975-12-31', NULL, 15,
     'LFT art. 87: aguinaldo minimo de 15 dias'),
    ('lft_prima_vacacional', '1970-05-01', NULL, 0.25,
     'LFT art. 80: prima vacacional minima del 25%')
ON CONFLICT DO NOTHING;

-- --- Cesantia en edad avanzada y vejez, cuota patronal escalonada ---------
-- Un renglon por rango de SBC y por anio. minimum_wage marca el renglon de
-- "1.00 SM"; los demas van hasta upper_uma veces la UMA (NULL = sin tope).
CREATE TABLE IF NOT EXISTS ceav_employer_rates (
    id SERIAL PRIMARY KEY,
    valid_from DATE NOT NULL,
    valid_to DATE,
    minimum_wage BOOLEAN NOT NULL DEFAULT FALSE,
    upper_uma NUMERIC(6, 2),
    rate NUMERIC(8, 6) NOT NULL CHECK (rate > 0),
    source TEXT NOT NULL,
    CHECK (NOT minimum_wage OR upper_uma IS NULL)
);

CREATE INDEX IF NOT EXISTS idx_ceav_employer_rates_valid
    ON ceav_employer_rates (valid_from, valid_to);

INSERT INTO ceav_employer_rates
    (valid_from, valid_to, minimum_wage, upper_uma, rate, source)
SELECT make_date(t.year, 1, 1), make_date(t.year, 12, 31),
       b.minimum_wage, b.upper_uma, t.rate,
       'Decreto DOF 16-12-2020, segundo transitorio (LSS art. 168 fr. II); '
       || 'tabla de la Nota de la Reforma de Pensiones, SHCP, enero 2021'
  FROM (VALUES
      (1, TRUE, NULL::NUMERIC),
      (2, FALSE, 1.50), (3, FALSE, 2.00), (4, FALSE, 2.50), (5, FALSE, 3.00),
      (6, FALSE, 3.50), (7, FALSE, 4.00), (8, FALSE, NULL::NUMERIC)
  ) AS b(position, minimum_wage, upper_uma)
  JOIN (VALUES
      (2023, 1, 0.03150), (2023, 2, 0.03281), (2023, 3, 0.03575),
      (2023, 4, 0.03751), (2023, 5, 0.03869), (2023, 6, 0.03953),
      (2023, 7, 0.04016), (2023, 8, 0.04241),
      (2024, 1, 0.03150), (2024, 2, 0.03413), (2024, 3, 0.04000),
      (2024, 4, 0.04353), (2024, 5, 0.04588), (2024, 6, 0.04756),
      (2024, 7, 0.04882), (2024, 8, 0.05331),
      (2025, 1, 0.03150), (2025, 2, 0.03544), (2025, 3, 0.04426),
      (2025, 4, 0.04954), (2025, 5, 0.05307), (2025, 6, 0.05559),
      (2025, 7, 0.05747), (2025, 8, 0.06422),
      (2026, 1, 0.03150), (2026, 2, 0.03676), (2026, 3, 0.04851),
      (2026, 4, 0.05556), (2026, 5, 0.06026), (2026, 6, 0.06361),
      (2026, 7, 0.06613), (2026, 8, 0.07513),
      (2027, 1, 0.03150), (2027, 2, 0.03807), (2027, 3, 0.05276),
      (2027, 4, 0.06157), (2027, 5, 0.06745), (2027, 6, 0.07164),
      (2027, 7, 0.07479), (2027, 8, 0.08603),
      (2028, 1, 0.03150), (2028, 2, 0.03939), (2028, 3, 0.05701),
      (2028, 4, 0.06759), (2028, 5, 0.07464), (2028, 6, 0.07967),
      (2028, 7, 0.08345), (2028, 8, 0.09694),
      (2029, 1, 0.03150), (2029, 2, 0.04070), (2029, 3, 0.06126),
      (2029, 4, 0.07360), (2029, 5, 0.08183), (2029, 6, 0.08770),
      (2029, 7, 0.09211), (2029, 8, 0.10784),
      (2030, 1, 0.03150), (2030, 2, 0.04202), (2030, 3, 0.06552),
      (2030, 4, 0.07962), (2030, 5, 0.08902), (2030, 6, 0.09573),
      (2030, 7, 0.10077), (2030, 8, 0.11875)
  ) AS t(year, position, rate) ON t.position = b.position
 WHERE NOT EXISTS (SELECT 1 FROM ceav_employer_rates);

-- A partir de 2031 la tabla final de 2030 sigue vigente (LSS art. 168 fr. II).
INSERT INTO ceav_employer_rates
    (valid_from, valid_to, minimum_wage, upper_uma, rate, source)
SELECT '2031-01-01', NULL, minimum_wage, upper_uma, rate,
       'LSS art. 168 fr. II a), tabla vigente al concluir la transicion'
  FROM ceav_employer_rates
 WHERE valid_from = '2030-01-01'
   AND NOT EXISTS (
       SELECT 1 FROM ceav_employer_rates WHERE valid_from = '2031-01-01'
   );

-- --- Impuesto sobre nominas por estado -------------------------------------
-- TODO: sin semilla. Las tasas cambian cada anio en las leyes locales y no se
-- confirmaron en una fuente oficial vigente. Mientras un estado no tenga
-- tasa, el ISN de sus recibos queda como pendiente. Para registrarla:
--   INSERT INTO state_payroll_tax_rates (entidad, valid_from, rate, source)
--   VALUES ('NLE', '2026-01-01', 0.03, 'Ley de Hacienda del Estado ... art. ...');
CREATE TABLE IF NOT EXISTS state_payroll_tax_rates (
    id SERIAL PRIMARY KEY,
    entidad CHAR(3) NOT NULL,
    valid_from DATE NOT NULL,
    valid_to DATE,
    rate NUMERIC(8, 6) NOT NULL CHECK (rate >= 0 AND rate < 0.2),
    source TEXT NOT NULL,
    CHECK (valid_to IS NULL OR valid_to >= valid_from),
    EXCLUDE USING gist (
        entidad WITH =,
        daterange(valid_from, valid_to, '[]') WITH &&
    )
);

-- --- Prima de riesgo de trabajo de cada empresa ----------------------------
-- La determina la propia empresa cada anio (LSS arts. 72 a 74): entre la
-- prima minima de 0.5% y la maxima de 15%.
CREATE TABLE IF NOT EXISTS company_risk_premiums (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    valid_from DATE NOT NULL,
    valid_to DATE,
    -- Siete decimales: la prima se declara con cinco en por ciento (0.54355%).
    rate NUMERIC(9, 7) NOT NULL CHECK (rate >= 0.005 AND rate <= 0.15),
    recorded_by INTEGER REFERENCES employees(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (valid_to IS NULL OR valid_to >= valid_from),
    CONSTRAINT company_risk_premiums_no_overlap EXCLUDE USING gist (
        company_id WITH =,
        daterange(valid_from, valid_to, '[]') WITH &&
    )
);

-- --- Costo patronal guardado por recibo ------------------------------------
-- Aparte de payroll_receipt_items a proposito: esas partidas son las que ve
-- el empleado y las que pinta su PDF; el costo patronal no es parte de su
-- recibo. Se guarda ya calculado para que el historico no cambie si mañana
-- cambian las tasas.
CREATE TABLE IF NOT EXISTS payroll_employer_costs (
    receipt_id INTEGER PRIMARY KEY
        REFERENCES payroll_receipts(id) ON DELETE CASCADE,
    daily_salary NUMERIC(12, 2) NOT NULL,
    integration_factor NUMERIC(8, 6) NOT NULL,
    sbc_daily NUMERIC(12, 2),
    uma_daily NUMERIC(12, 2),
    days NUMERIC(5, 2) NOT NULL,
    total NUMERIC(12, 2) NOT NULL,
    missing TEXT[] NOT NULL DEFAULT '{}',
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payroll_employer_cost_items (
    id SERIAL PRIMARY KEY,
    receipt_id INTEGER NOT NULL
        REFERENCES payroll_employer_costs(receipt_id) ON DELETE CASCADE,
    component VARCHAR(40) NOT NULL,
    group_key VARCHAR(12) NOT NULL
        CHECK (group_key IN ('imss', 'sar', 'infonavit', 'isn')),
    description VARCHAR(120) NOT NULL,
    base NUMERIC(14, 2) NOT NULL,
    rate NUMERIC(12, 8) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    position SMALLINT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_payroll_employer_cost_items_receipt
    ON payroll_employer_cost_items (receipt_id, position);
