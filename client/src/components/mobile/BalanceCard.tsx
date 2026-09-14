import { ReactNode } from "react";

interface BalanceCardProps {
  label: string;
  amount: number;
  currency?: string;
  status: "paid" | "pending" | "failed";
  period: string;
  badge?: ReactNode;
}

export function BalanceCard({
  label,
  amount,
  currency = "$",
  status,
  period,
  badge,
}: BalanceCardProps) {
  const statusConfig = {
    paid: { className: "badge-success", text: "PAGADO" },
    pending: { className: "badge-warning", text: "PENDIENTE" },
    failed: { className: "badge-danger", text: "FALLIDO" },
  };

  const config = statusConfig[status];

  return (
    <div className="balance-card">
      <div className="balance-label">{label}</div>
      <div className="balance-amount">
        {currency}
        {amount.toLocaleString("es-MX")}
      </div>
      <div className="balance-footer">
        <span className="balance-period">{period}</span>
        <span className={`badge ${config.className}`}>
          {badge || config.text}
        </span>
      </div>
    </div>
  );
}
