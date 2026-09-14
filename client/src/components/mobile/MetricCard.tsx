interface MetricCardProps {
  label: string;
  value: number | string;
  trend?: "up" | "down";
  icon?: string;
}

export function MetricCard({ label, value, trend, icon }: MetricCardProps) {
  return (
    <div className="metric-card">
      {icon && <div className="metric-icon">{icon}</div>}
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      {trend && <div className={`metric-trend trend-${trend}`} />}
    </div>
  );
}
