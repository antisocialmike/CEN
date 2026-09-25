import { useId, useState } from "react";

export interface StackSeries {
  key: string;
  name: string;
  // Un token de color (var(--viz-...)); nunca se usa para texto.
  color: string;
}

export interface StackColumn {
  key: string;
  label: string;
  values: Record<string, number>;
  // Renglones extra del tooltip, como el porcentaje sobre la nomina.
  extra?: { label: string; value: string }[];
}

interface StackedColumnChartProps {
  label: string;
  series: StackSeries[];
  columns: StackColumn[];
  formatValue: (value: number) => string;
}

// Columnas apiladas de pocas series con leyenda arriba. Cada columna es su
// propio blanco de puntero y de foco: el tooltip lista todas las series del mes.
export default function StackedColumnChart({
  label,
  series,
  columns,
  formatValue
}: StackedColumnChartProps) {
  const tooltipId = useId();
  const [active, setActive] = useState<number | null>(null);
  const totals = columns.map((column) =>
    series.reduce((sum, item) => sum + (column.values[item.key] ?? 0), 0)
  );
  const max = Math.max(0, ...totals);
  const current = active === null ? null : columns[active];

  return (
    <div className="viz-stack">
      <ul className="viz-legend" aria-hidden="true">
        {series.map((item) => (
          <li key={item.key}>
            <span className="viz-key-rect" style={{ background: item.color }} />
            {item.name}
          </li>
        ))}
      </ul>

      <ol className="viz-stack-columns" aria-label={label}>
        {columns.map((column, index) => (
          <li
            key={column.key}
            className={index === active ? "viz-stack-column is-active" : "viz-stack-column"}
            tabIndex={0}
            aria-label={`${column.label}: ${formatValue(totals[index])}`}
            aria-describedby={index === active ? tooltipId : undefined}
            onPointerEnter={() => setActive(index)}
            onPointerLeave={() => setActive(null)}
            onFocus={() => setActive(index)}
            onBlur={() => setActive(null)}
          >
            <span className="viz-stack-slot">
              <span
                className="viz-stack-bar"
                style={{ height: `${max > 0 ? (totals[index] / max) * 100 : 0}%` }}
              >
                {series.map((item) => {
                  const value = column.values[item.key] ?? 0;
                  return value > 0 ? (
                    <span
                      key={item.key}
                      className="viz-stack-segment"
                      style={{ flexGrow: value, background: item.color }}
                    />
                  ) : null;
                })}
              </span>
            </span>
            <span className="viz-column-label">{column.label}</span>
          </li>
        ))}
      </ol>

      {current && active !== null && (
        <div
          id={tooltipId}
          className="viz-tooltip viz-stack-tooltip"
          role="status"
          style={{ left: `${((active + 0.5) / columns.length) * 100}%` }}
        >
          <p className="viz-tooltip-title">{current.label}</p>
          {series.map((item) => (
            <p key={item.key} className="viz-tooltip-row">
              <span className="viz-key-line" style={{ background: item.color }} />
              <strong>{formatValue(current.values[item.key] ?? 0)}</strong>
              <span>{item.name}</span>
            </p>
          ))}
          <p className="viz-tooltip-row is-extra">
            <span className="viz-key-line is-empty" />
            <strong>{formatValue(totals[active])}</strong>
            <span>Total</span>
          </p>
          {current.extra?.map((row) => (
            <p key={row.label} className="viz-tooltip-row is-extra">
              <span className="viz-key-line is-empty" />
              <strong>{row.value}</strong>
              <span>{row.label}</span>
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
