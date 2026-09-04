import { motion } from "motion/react";
import { PayrollBreakdown } from "../services/payrollService";

interface PayrollResultCardProps {
  breakdown: PayrollBreakdown;
}

function formatCurrency(value: number): string {
  return value.toLocaleString("es-MX", {
    style: "currency",
    currency: "MXN",
    minimumFractionDigits: 2
  });
}

export default function PayrollResultCard({ breakdown }: PayrollResultCardProps) {
  return (
    <motion.div
      className="payroll-result"
      initial={{ opacity: 0, y: 12, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
    >
      <div className="payroll-result-row">
        <span>Salario bruto</span>
        <span>{formatCurrency(breakdown.gross_salary)}</span>
      </div>
      <div className="payroll-result-row deduction">
        <span>ISR</span>
        <span>− {formatCurrency(breakdown.isr_deduction)}</span>
      </div>
      <div className="payroll-result-row deduction">
        <span>IMSS</span>
        <span>− {formatCurrency(breakdown.imss_deduction)}</span>
      </div>
      <div className="payroll-result-row total">
        <span>Neto a pagar</span>
        <span>{formatCurrency(breakdown.net_salary)}</span>
      </div>
    </motion.div>
  );
}
