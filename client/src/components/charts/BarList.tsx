export interface BarItem {
  id: string | number;
  label: string;
  detail?: string;
  value: number;
  // Si la barra pertenece a un grupo con su propio color; si no, el de la lista.
  color?: string;
}

interface BarListProps {
  label: string;
  items: BarItem[];
  color: string;
  formatValue: (value: number) => string;
}

// Barras horizontales de una sola serie: el valor va en la punta de cada una,
// asi que no necesitan tooltip para leerse.
export default function BarList({ label, items, color, formatValue }: BarListProps) {
  const max = Math.max(0, ...items.map((item) => item.value));

  return (
    <ul className="viz-bars" aria-label={label}>
      {items.map((item) => {
        const share = max > 0 ? (item.value / max) * 100 : 0;
        return (
          <li key={item.id} className="viz-bar-row">
            <p className="viz-bar-label">
              {item.label}
              {item.detail && <span>{item.detail}</span>}
            </p>
            <div className="viz-bar-track">
              <span
                className="viz-bar"
                style={{
                  width: `${Math.max(share, item.value > 0 ? 1 : 0)}%`,
                  background: item.color ?? color
                }}
              />
              <span className="viz-bar-value">{formatValue(item.value)}</span>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
