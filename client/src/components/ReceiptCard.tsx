import PayrollBreakdownRows from "./PayrollBreakdownRows";
import ReceiptDownloadButton from "./ReceiptDownloadButton";
import { PayrollReceipt } from "../services/payrollService";
import {
  formatCurrency,
  formatMonth,
  formatRange
} from "../services/format";

interface ReceiptCardProps {
  receipt: PayrollReceipt;
}

export default function ReceiptCard({ receipt }: ReceiptCardProps) {
  return (
    <article className="receipt-card">
      <header className="receipt-card-header">
        <div className="receipt-card-period">
          <p className="receipt-card-month">
            {formatMonth(receipt.period_start)}
          </p>
          <p className="receipt-card-date">
            Recibo #{receipt.id}
            {receipt.company_name && ` · ${receipt.company_name}`} ·{" "}
            {formatRange(receipt.period_start, receipt.period_end)}
            {receipt.tipo_regimen === "09" && " · Honorarios asimilados a salarios"}
          </p>
        </div>

        <div className="receipt-card-net-group">
          <p className="receipt-card-net-label">Neto</p>
          <p className="receipt-card-net">{formatCurrency(receipt.net_salary)}</p>
        </div>
      </header>

      <PayrollBreakdownRows
        items={receipt.items}
        totalPerceptions={receipt.total_perceptions}
        totalDeductions={receipt.total_deductions}
      />

      <footer className="receipt-card-footer">
        <ReceiptDownloadButton receiptId={receipt.id} />
      </footer>
    </article>
  );
}
