import { motion } from "motion/react";
import { PayrollReceipt } from "../services/payrollService";

interface ReceiptCardProps {
  receipt: PayrollReceipt;
  index: number;
}

function formatCurrency(value: number): string {
  return value.toLocaleString("es-MX", {
    style: "currency",
    currency: "MXN",
    minimumFractionDigits: 2
  });
}

function formatDate(value: string): string {
  const formatted = new Date(value).toLocaleDateString("es-MX", {
    year: "numeric",
    month: "long",
    day: "numeric"
  });
  return formatted.charAt(0).toUpperCase() + formatted.slice(1);
}

export default function ReceiptCard({ receipt, index }: ReceiptCardProps) {
  return (
    <motion.div
      className="receipt-card"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05, ease: "easeOut" }}
    >
      <div className="receipt-card-header">
        <span className="receipt-card-date">{formatDate(receipt.created_at)}</span>
        <span className="receipt-card-net">{formatCurrency(receipt.net_salary)}</span>
      </div>
      <div className="payroll-result-row">
        <span>Salario bruto</span>
        <span>{formatCurrency(receipt.gross_salary)}</span>
      </div>
      <div className="payroll-result-row deduction">
        <span>ISR</span>
        <span>− {formatCurrency(receipt.isr_deduction)}</span>
      </div>
      <div className="payroll-result-row deduction">
        <span>IMSS</span>
        <span>− {formatCurrency(receipt.imss_deduction)}</span>
      </div>
    </motion.div>
  );
}
