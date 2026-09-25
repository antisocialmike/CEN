import { Info } from "@phosphor-icons/react";
import StackedColumnChart from "./charts/StackedColumnChart";
import BarList from "./charts/BarList";
import ChartTable from "./charts/ChartTable";
import {
  EmployerCost,
  EmployerCostGroup,
  EmployerCostMonth,
  toAmount
} from "../services/ownerService";
import { formatCurrency, formatInteger, formatMonth, formatMonthShort } from "../services/format";

// Orden y colores validados como paleta categorica sobre las tarjetas en
// claro y oscuro (violeta, naranja, azul, magenta). El magenta queda bajo 3:1
// en claro: por eso cada grafica lleva leyenda y tabla.
const GROUPS: { key: EmployerCostGroup; name: string; color: string }[] = [
  { key: "imss", name: "Cuotas IMSS", color: "var(--viz-imss)" },
  { key: "sar", name: "Retiro, cesantía y vejez", color: "var(--viz-sar)" },
  { key: "infonavit", name: "INFONAVIT", color: "var(--viz-infonavit)" },
  { key: "isn", name: "Impuesto sobre nóminas", color: "var(--viz-isn)" }
];

const MISSING_LABELS: Record<string, string> = {
  isn: "la tasa del impuesto sobre nóminas del estado",
  prima_riesgo_trabajo: "la prima de riesgo de trabajo de la empresa",
  uma_diaria: "la UMA vigente",
  salario_minimo_general: "el salario mínimo vigente",
  ceav: "la tabla de cesantía y vejez",
  sbc: "el salario base de cotización"
};

function groupOf(key: EmployerCostGroup) {
  return GROUPS.find((group) => group.key === key) ?? GROUPS[0];
}

function monthTotal(month: EmployerCostMonth): number {
  return GROUPS.reduce((sum, group) => sum + toAmount(month[group.key]), 0);
}

function percentOf(part: number, whole: number): string | null {
  return whole > 0 ? `${((part / whole) * 100).toFixed(1)} %` : null;
}

function receipts(count: number): string {
  return `${formatInteger(count)} ${count === 1 ? "recibo" : "recibos"}`;
}

interface EmployerCostSectionProps {
  employerCost: EmployerCost;
  employerCostPct: string | null;
}

export default function EmployerCostSection({
  employerCost,
  employerCostPct
}: EmployerCostSectionProps) {
  const { coverage, components, missing, monthly } = employerCost;
  const notices: string[] = [];

  if (coverage.receipts_without_cost > 0) {
    notices.push(
      `${receipts(coverage.receipts_without_cost)} del periodo se calcularon antes de que existiera el costo patronal y no lo incluyen.`
    );
  }
  for (const item of missing) {
    notices.push(
      `${receipts(item.receipts)} sin ${MISSING_LABELS[item.name] ?? item.name}: ese componente no está sumado.`
    );
  }

  return (
    <section className="owner-card" aria-labelledby="titulo-patronal">
      <h2 id="titulo-patronal">Costo patronal</h2>
      <p className="owner-card-note">
        Lo que la empresa paga encima de la nómina: cuotas del IMSS, retiro, INFONAVIT e impuesto
        estatal.
        {employerCostPct !== null && ` En el periodo equivale al ${employerCostPct} % de la nómina.`}
      </p>

      {notices.length > 0 && (
        <ul className="owner-notices">
          {notices.map((notice) => (
            <li key={notice}>
              <Info weight="bold" aria-hidden="true" />
              {notice}
            </li>
          ))}
        </ul>
      )}

      {coverage.receipts_with_cost === 0 ? (
        <p className="owner-card-note">
          Todavía no hay recibos con costo patronal en este periodo. Se calcula en cada nómina
          nueva.
        </p>
      ) : (
        <>
          <StackedColumnChart
            label="Costo patronal por mes y por grupo"
            series={GROUPS}
            formatValue={formatCurrency}
            columns={monthly.map((month) => {
              const share = percentOf(monthTotal(month), toAmount(month.covered_gross));
              return {
                key: month.month,
                label: formatMonthShort(month.month),
                values: Object.fromEntries(
                  GROUPS.map((group) => [group.key, toAmount(month[group.key])])
                ),
                extra: share ? [{ label: "de la nómina", value: share }] : []
              };
            })}
          />
          <ChartTable
            caption="Costo patronal por mes"
            columns={[
              { label: "Mes" },
              ...GROUPS.map((group) => ({ label: group.name, numeric: true })),
              { label: "Total", numeric: true }
            ]}
            rows={monthly.map((month) => ({
              key: month.month,
              cells: [
                formatMonth(month.month),
                ...GROUPS.map((group) => formatCurrency(toAmount(month[group.key]))),
                formatCurrency(monthTotal(month))
              ]
            }))}
          />

          <h3 className="owner-subtitle">Por componente</h3>
          <BarList
            label="Costo patronal por componente"
            color="var(--viz-imss)"
            formatValue={formatCurrency}
            items={components.map((component) => ({
              id: component.component,
              label: component.description,
              detail: groupOf(component.group_key).name,
              value: toAmount(component.amount),
              color: groupOf(component.group_key).color
            }))}
          />
          <ChartTable
            caption="Costo patronal por componente"
            columns={[{ label: "Componente" }, { label: "Grupo" }, { label: "Importe", numeric: true }]}
            rows={components.map((component) => ({
              key: component.component,
              cells: [
                component.description,
                groupOf(component.group_key).name,
                formatCurrency(toAmount(component.amount))
              ]
            }))}
          />
        </>
      )}
    </section>
  );
}
