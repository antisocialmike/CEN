import { motion } from "motion/react";
import PayrollBreakdownRows from "./PayrollBreakdownRows";
import ReceiptDownloadButton from "./ReceiptDownloadButton";
import { PayrollCalculationResult } from "../services/payrollService";
import { formatCurrency, formatMonth } from "../services/format";

interface PayrollResultCardProps {
  result: PayrollCalculationResult;
}

export default function PayrollResultCard({ result }: PayrollResultCardProps) {
  const { data: breakdown } = result;

  return (
    <motion.div
      className="payroll-result"
      role="status"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
    >
      <p className="payroll-result-heading">
        <span>Desglose de {formatMonth(result.period_start)}</span>
        <small>Recibo #{result.receipt_id}</small>
      </p>

      <PayrollBreakdownRows
        items={breakdown.items}
        totalPerceptions={breakdown.total_perceptions}
        totalDeductions={breakdown.total_deductions}
      />
      <div className="payroll-result-row total">
        <span>Neto a pagar</span>
        <span>{formatCurrency(breakdown.net_salary)}</span>
      </div>

      <p className="payroll-result-footer">
        {result.created ? "Guardado como recibo" : "Recibo reemplazado"} #{result.receipt_id}
        {result.employee_name ? ` de ${result.employee_name}` : ""}. Ya es visible en su portal.
      </p>

      <div className="receipt-card-footer">
        <ReceiptDownloadButton receiptId={result.receipt_id} />
      </div>
    </motion.div>
  );
}
