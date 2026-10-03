import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import { ArrowDown, ArrowUp, Buildings, ChartLineUp, Minus } from "@phosphor-icons/react";
import { rowVariants, stackVariants, useStill } from "../motion/variants";
import EsqueletoPanel from "../components/EsqueletoPanel";
import ErrorMessage from "../components/ErrorMessage";
import SelectField from "../components/SelectField";
import TrendChart, { TrendPoint } from "../components/charts/TrendChart";
import BarList from "../components/charts/BarList";
import ColumnChart from "../components/charts/ColumnChart";
import ChartTable from "../components/charts/ChartTable";
import EmployerCostSection from "../components/EmployerCostSection";
import {
  Amount,
  getAnalytics,
  listOwnerCompanies,
  OwnerCompany,
  PayrollAnalytics,
  toAmount
} from "../services/ownerService";
import {
  DEFAULT_PRESET,
  isPeriodPreset,
  PERIOD_PRESETS,
  PeriodPreset,
  resolvePreset,
  withoutEmptyCurrentMonth
} from "../services/analyticsPeriods";
import {
  formatChange,
  formatCurrency,
  formatCurrencyCompact,
  formatInteger,
  formatMonth,
  formatMonthShort
} from "../services/format";
import "../styles/skin-dueno.css";

const PERCEPCION = "var(--viz-percepcion)";
const DEDUCCION = "var(--viz-deduccion)";

type CompanyFilter = number | "all";

function parseCompany(raw: string | null): CompanyFilter {
  const id = Number(raw);
  return raw !== null && Number.isInteger(id) && id > 0 ? id : "all";
}

interface KpiTileProps {
  label: string;
  value: string;
  change?: Amount | null;
  detail?: string;
}

// Un alza de nomina no es buena ni mala por si misma: la flecha dice hacia
// donde fue y el texto se queda en tinta neutra.
function KpiTile({ label, value, change, detail }: KpiTileProps) {
  const direction = change == null ? 0 : Math.sign(Number(change));
  const Icon = direction > 0 ? ArrowUp : direction < 0 ? ArrowDown : Minus;

  return (
    <div className="stat-card kpi-card">
      <p className="stat-card-label">{label}</p>
      <p className="stat-card-value">{value}</p>
      {detail && <p className="kpi-detail">{detail}</p>}
      {change !== undefined && (
        <p className="kpi-delta">
          <Icon weight="bold" aria-hidden="true" />
          <span>
            {formatChange(change)}
            {change !== null && <span className="visually-hidden"> contra el periodo anterior</span>}
          </span>
        </p>
      )}
    </div>
  );
}

function kpiTiles(kpis: PayrollAnalytics["kpis"]): KpiTileProps[] {
  const money = (value: Amount | null) =>
    value === null ? "—" : formatCurrency(toAmount(value));
  return [
    {
      label: "Costo total para la empresa",
      value: money(kpis.total_cost),
      change: kpis.change.total_cost,
      detail: "Nómina bruta más costo patronal"
    },
    { label: "Nómina bruta", value: money(kpis.gross_payroll), change: kpis.change.gross_payroll },
    {
      label: "Costo patronal",
      value: money(kpis.employer_cost),
      change: kpis.change.employer_cost,
      detail:
        kpis.employer_cost_pct === null ? undefined : `${kpis.employer_cost_pct} % de la nómina`
    },
    { label: "Neto pagado", value: money(kpis.net_paid), change: kpis.change.net_paid },
    { label: "ISR retenido", value: money(kpis.isr_withheld), change: kpis.change.isr_withheld },
    { label: "IMSS retenido", value: money(kpis.imss_withheld), change: kpis.change.imss_withheld },
    {
      label: "Costo por persona en el periodo",
      value: money(kpis.average_cost_per_employee),
      change: kpis.change.average_cost_per_employee
    },
    { label: "Empleados activos hoy", value: formatInteger(kpis.active_employees) }
  ];
}

export default function OwnerDashboardPage() {
  const stackTravel = useStill(stackVariants);
  const rowTravel = useStill(rowVariants);
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [companies, setCompanies] = useState<OwnerCompany[] | null>(null);
  // La ultima respuesta y los filtros que la pidieron: mientras llega la de los
  // filtros nuevos se sigue viendo la anterior, atenuada, sin saltos.
  const [shown, setShown] = useState<{ key: string; analytics: PayrollAnalytics } | null>(null);
  const [failedKey, setFailedKey] = useState<string | null>(null);

  const company = parseCompany(searchParams.get("empresa"));
  const rawPreset = searchParams.get("periodo");
  const preset: PeriodPreset = isPeriodPreset(rawPreset) ? rawPreset : DEFAULT_PRESET;
  const requestKey = `${company}|${preset}`;
  const analytics = shown?.analytics ?? null;
  const errorMessage =
    failedKey === requestKey
      ? "No se pudieron cargar las cifras. Revisa tu conexión y vuelve a intentarlo."
      : null;
  const isLoading = shown?.key !== requestKey && errorMessage === null;

  function updateFilter(key: "empresa" | "periodo", value: string) {
    setSearchParams(
      (current) => {
        const next = new URLSearchParams(current);
        next.set(key, value);
        return next;
      },
      { replace: true }
    );
  }

  useEffect(() => {
    let isMounted = true;
    listOwnerCompanies()
      .then((list) => isMounted && setCompanies(list))
      .catch(() => isMounted && setCompanies([]));
    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    let isMounted = true;
    const { from, to } = resolvePreset(preset, new Date());
    const key = `${company}|${preset}`;

    getAnalytics({ companyId: company, from, to })
      .then((result) => {
        if (!isMounted) return;
        setShown({ key, analytics: withoutEmptyCurrentMonth(result, new Date()) });
        setFailedKey(null);
      })
      .catch(() => isMounted && setFailedKey(key));

    return () => {
      isMounted = false;
    };
  }, [company, preset]);

  const trendPoints = useMemo<TrendPoint[]>(
    () =>
      (analytics?.monthly ?? []).map((month) => ({
        key: month.month,
        label: formatMonthShort(month.month),
        values: [toAmount(month.gross_payroll), toAmount(month.total_deductions)]
      })),
    [analytics]
  );

  if (analytics === null && errorMessage === null) {
    return <EsqueletoPanel />;
  }

  const kpis = analytics?.kpis;
  const perceptions = analytics?.concepts.filter((concept) => concept.kind === "perception") ?? [];
  const deductions = analytics?.concepts.filter((concept) => concept.kind === "deduction") ?? [];
  const movements = analytics?.headcount.by_month.filter(
    (month) => month.hires > 0 || month.terminations > 0
  ) ?? [];
  const isEmpty = kpis !== undefined && kpis.receipts === 0 && kpis.active_employees === 0;
  const presetLabel = PERIOD_PRESETS.find((item) => item.value === preset)?.label ?? "";

  return (
    <div className="dashboard-panel owner-dashboard">
      <div className="dashboard-panel-header">
        <div className="dashboard-panel-heading">
          <div>
            <h1>Tablero</h1>
            <p className="dashboard-panel-subtitle">
              Lo que cuesta la nómina de tus empresas y cómo cambia. Los recibos cuentan en el mes
              en que empieza su periodo.
            </p>
          </div>
        </div>
        <button className="btn btn-line" onClick={() => navigate("/dueno/empresas")}>
          <Buildings weight="bold" />
          Mis empresas
        </button>
      </div>

      <div className="owner-filters">
        <SelectField
          id="filtro-empresa"
          label="Empresa"
          value={String(company)}
          onChange={(value) => updateFilter("empresa", value)}
          options={[
            { value: "all", label: "Todas las empresas" },
            ...(companies ?? []).map((item) => ({
              value: String(item.id),
              label: (item.trade_name || item.legal_name) + (item.is_active ? "" : " (inactiva)")
            }))
          ]}
        />
        <fieldset className="owner-presets">
          <legend>Periodo</legend>
          {PERIOD_PRESETS.map((item) => (
            <label key={item.value} className={item.value === preset ? "is-selected" : undefined}>
              <input
                type="radio"
                name="periodo"
                value={item.value}
                checked={item.value === preset}
                onChange={() => updateFilter("periodo", item.value)}
              />
              {item.label}
            </label>
          ))}
        </fieldset>
      </div>

      <AnimatePresence mode="wait">
        {errorMessage && <ErrorMessage key="error" message={errorMessage} />}
      </AnimatePresence>

      {analytics && kpis && (
        <div className={isLoading ? "owner-body is-refreshing" : "owner-body"} aria-busy={isLoading}>
          {isEmpty ? (
            <div className="empty-state">
              <span className="empty-state-icon" aria-hidden="true">
                <ChartLineUp weight="bold" />
              </span>
              <p className="empty-state-title">Todavía no hay nómina que mostrar</p>
              <p>
                Cuando los administradores calculen recibos en {presetLabel.toLowerCase()}, las
                cifras aparecerán aquí.
              </p>
            </div>
          ) : (
            <>
              <motion.div
                className="stat-row kpi-row"
                variants={stackTravel}
                initial="initial"
                animate="animate"
              >
                {kpiTiles(kpis).map((tile) => (
                  <motion.div key={tile.label} variants={rowTravel}>
                    <KpiTile {...tile} />
                  </motion.div>
                ))}
              </motion.div>

              <section className="owner-card" aria-labelledby="titulo-tendencia">
                <h2 id="titulo-tendencia">Nómina por mes</h2>
                <p className="owner-card-note">
                  {formatInteger(kpis.receipts)} recibos de {formatInteger(kpis.paid_employees)}{" "}
                  personas en el periodo.
                </p>
                <TrendChart
                  label="Percepciones y deducciones por mes"
                  series={[
                    { name: "Percepciones", color: PERCEPCION, kind: "area" },
                    { name: "Deducciones", color: DEDUCCION, kind: "line" }
                  ]}
                  points={trendPoints}
                  formatValue={formatCurrency}
                  formatTick={formatCurrencyCompact}
                  extraRows={(point) => {
                    const month = analytics.monthly.find((item) => item.month === point.key);
                    return month
                      ? [{ label: "Neto pagado", value: formatCurrency(toAmount(month.net_paid)) }]
                      : [];
                  }}
                />
                <ChartTable
                  caption="Nómina por mes"
                  columns={[
                    { label: "Mes" },
                    { label: "Percepciones", numeric: true },
                    { label: "Deducciones", numeric: true },
                    { label: "Neto", numeric: true },
                    { label: "Recibos", numeric: true }
                  ]}
                  rows={analytics.monthly.map((month) => ({
                    key: month.month,
                    cells: [
                      formatMonth(month.month),
                      formatCurrency(toAmount(month.gross_payroll)),
                      formatCurrency(toAmount(month.total_deductions)),
                      formatCurrency(toAmount(month.net_paid)),
                      formatInteger(month.receipts)
                    ]
                  }))}
                />
              </section>

              <EmployerCostSection
                employerCost={analytics.employer_cost}
                employerCostPct={kpis.employer_cost_pct}
              />

              <div className="owner-grid">
                {[
                  { id: "percepciones", title: "Percepciones por concepto", items: perceptions, color: PERCEPCION },
                  { id: "deducciones", title: "Deducciones por concepto", items: deductions, color: DEDUCCION }
                ].map((group) => (
                  <section key={group.id} className="owner-card" aria-labelledby={"titulo-" + group.id}>
                    <h2 id={"titulo-" + group.id}>{group.title}</h2>
                    {group.items.length === 0 ? (
                      <p className="owner-card-note">Sin movimientos en el periodo.</p>
                    ) : (
                      <>
                        <BarList
                          label={group.title}
                          color={group.color}
                          formatValue={formatCurrency}
                          items={group.items.map((concept) => ({
                            id: concept.concept,
                            label: concept.description,
                            detail:
                              toAmount(concept.exempt) > 0
                                ? `${formatCurrency(toAmount(concept.exempt))} exento`
                                : undefined,
                            value: toAmount(concept.amount)
                          }))}
                        />
                        <ChartTable
                          caption={group.title}
                          columns={[
                            { label: "Concepto" },
                            { label: "Importe", numeric: true },
                            { label: "Gravado", numeric: true },
                            { label: "Exento", numeric: true }
                          ]}
                          rows={group.items.map((concept) => ({
                            key: concept.concept,
                            cells: [
                              concept.description,
                              formatCurrency(toAmount(concept.amount)),
                              formatCurrency(toAmount(concept.taxable)),
                              formatCurrency(toAmount(concept.exempt))
                            ]
                          }))}
                        />
                      </>
                    )}
                  </section>
                ))}
              </div>

              {analytics.companies.length > 1 && (
                <section className="owner-card" aria-labelledby="titulo-empresas">
                  <h2 id="titulo-empresas">Comparativo entre empresas</h2>
                  <p className="owner-card-note">
                    Nómina bruta de cada empresa en el periodo. La tabla suma su costo patronal.
                  </p>
                  <BarList
                    label="Nómina bruta por empresa"
                    color={PERCEPCION}
                    formatValue={formatCurrency}
                    items={analytics.companies.map((item) => ({
                      id: item.id,
                      label: item.legal_name,
                      detail: `${formatInteger(item.active_employees)} ${item.active_employees === 1 ? "activo" : "activos"}${item.is_active ? "" : " · inactiva"}`,
                      value: toAmount(item.gross_payroll)
                    }))}
                  />
                  <ChartTable
                    caption="Comparativo entre empresas"
                    columns={[
                      { label: "Empresa" },
                      { label: "Nómina bruta", numeric: true },
                      { label: "Costo patronal", numeric: true },
                      { label: "Costo total", numeric: true },
                      { label: "Neto pagado", numeric: true },
                      { label: "Recibos", numeric: true },
                      { label: "Activos", numeric: true }
                    ]}
                    rows={analytics.companies.map((item) => ({
                      key: item.id,
                      cells: [
                        item.legal_name,
                        formatCurrency(toAmount(item.gross_payroll)),
                        formatCurrency(toAmount(item.employer_cost)),
                        formatCurrency(toAmount(item.total_cost)),
                        formatCurrency(toAmount(item.net_paid)),
                        formatInteger(item.receipts),
                        formatInteger(item.active_employees)
                      ]
                    }))}
                  />
                </section>
              )}

              <div className="owner-grid">
                <section className="owner-card" aria-labelledby="titulo-plantilla">
                  <h2 id="titulo-plantilla">Plantilla</h2>
                  <p className="owner-headcount">
                    <strong>{formatInteger(analytics.headcount.active)}</strong> activos
                    <span aria-hidden="true"> · </span>
                    <strong>{formatInteger(analytics.headcount.inactive)}</strong> dados de baja
                  </p>
                  {movements.length === 0 ? (
                    <p className="owner-card-note">Sin altas ni bajas registradas en el periodo.</p>
                  ) : (
                    <div className="table-wrap">
                      <table className="data-table owner-compact-table">
                        <caption className="visually-hidden">Altas y bajas por mes</caption>
                        <thead>
                          <tr>
                            <th scope="col">Mes</th>
                            <th scope="col" className="num">Altas</th>
                            <th scope="col" className="num">Bajas</th>
                          </tr>
                        </thead>
                        <tbody>
                          {movements.map((month) => (
                            <tr key={month.month}>
                              <td>{formatMonth(month.month)}</td>
                              <td className="num">{formatInteger(month.hires)}</td>
                              <td className="num">{formatInteger(month.terminations)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </section>

                <section className="owner-card" aria-labelledby="titulo-rangos">
                  <h2 id="titulo-rangos">Salarios base por rango</h2>
                  <p className="owner-card-note">Personas activas según su salario mensual.</p>
                  <ColumnChart
                    label="Personas activas por rango de salario"
                    color={PERCEPCION}
                    formatValue={formatInteger}
                    items={analytics.salary_histogram.map((bucket) => ({
                      label: bucket.label,
                      value: bucket.employees
                    }))}
                  />
                  <ChartTable
                    caption="Personas activas por rango de salario"
                    columns={[{ label: "Rango" }, { label: "Personas", numeric: true }]}
                    rows={analytics.salary_histogram.map((bucket) => ({
                      key: bucket.label,
                      cells: [bucket.label, formatInteger(bucket.employees)]
                    }))}
                  />
                </section>
              </div>

              {analytics.top_salaries.length > 0 && (
                <section className="owner-card" aria-labelledby="titulo-salarios">
                  <h2 id="titulo-salarios">Salarios más altos</h2>
                  <div className="table-wrap">
                    <table className="data-table">
                      <caption className="visually-hidden">Los cinco salarios base más altos</caption>
                      <thead>
                        <tr>
                          <th scope="col">Persona</th>
                          <th scope="col">Empresa</th>
                          <th scope="col" className="num">Salario base mensual</th>
                        </tr>
                      </thead>
                      <tbody>
                        {analytics.top_salaries.map((person) => (
                          <tr key={person.id}>
                            <td className="name">{person.name}</td>
                            <td>{person.company_name}</td>
                            <td className="num">{formatCurrency(toAmount(person.base_salary))}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
