export interface ColumnItem {
  label: string;
  value: number;
}

interface ColumnChartProps {
  label: string;
  items: ColumnItem[];
  color: string;
  formatValue: (value: number) => string;
}

// Columnas de una sola serie con el valor sobre cada una. Las vacias dejan
// solo la linea base para que el hueco se lea como cero y no como un error.
export default function ColumnChart({ label, items, color, formatValue }: ColumnChartProps) {
  const max = Math.max(0, ...items.map((item) => item.value));

  return (
    <ul className="viz-columns" aria-label={label}>
      {items.map((item) => (
        <li key={item.label} className="viz-column">
          <span className="viz-column-value">{formatValue(item.value)}</span>
          <span className="viz-column-slot">
            <span
              className="viz-column-bar"
              style={{ height: `${max > 0 ? (item.value / max) * 100 : 0}%`, background: color }}
            />
          </span>
          <span className="viz-column-label">{item.label}</span>
        </li>
      ))}
    </ul>
  );
}
