import { Receipt } from "@phosphor-icons/react";
import PayrollBreakdownRows from "./PayrollBreakdownRows";
import ReceiptDownloadButton from "./ReceiptDownloadButton";
import { PayrollReceipt } from "../services/payrollService";
import { formatCurrency, formatDateShort, formatMonth } from "../services/format";

interface ReceiptCardProps {
  receipt: PayrollReceipt;
}

export default function ReceiptCard({ receipt }: ReceiptCardProps) {
  return (
    <article className="receipt-card">
      <header className="receipt-card-header">
        <span className="receipt-card-period">
          <span className="receipt-card-icon" aria-hidden="true">
            <Receipt weight="bold" />
          </span>

          <span>
            <p className="receipt-card-month">{formatMonth(receipt.period)}</p>
            <p className="receipt-card-date">
              Recibo #{receipt.id} · emitido el {formatDateShort(receipt.created_at)}
            </p>
          </span>
        </span>

        <span className="receipt-card-net-group">
          <p className="receipt-card-net-label">Neto</p>
          <p className="receipt-card-net">{formatCurrency(receipt.net_salary)}</p>
        </span>
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
