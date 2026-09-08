import { Receipt } from "@phosphor-icons/react";
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

      <div className="payroll-result-row">
        <span>Salario bruto</span>
        <span>{formatCurrency(receipt.gross_salary)}</span>
      </div>
      <div className="payroll-result-row">
        <span>ISR retenido</span>
        <span>− {formatCurrency(receipt.isr_deduction)}</span>
      </div>
      <div className="payroll-result-row">
        <span>IMSS retenido</span>
        <span>− {formatCurrency(receipt.imss_deduction)}</span>
      </div>

      <footer className="receipt-card-footer">
        <ReceiptDownloadButton receiptId={receipt.id} />
      </footer>
    </article>
  );
}
