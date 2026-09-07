import { motion } from "motion/react";
import { PayrollCalculationResult } from "../services/payrollService";
import { formatCurrency } from "../services/format";

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
        <span>Desglose de nómina</span>
        <small>Recibo #{result.receipt_id}</small>
      </p>

      <div className="payroll-result-row">
        <span>Salario bruto</span>
        <span>{formatCurrency(breakdown.gross_salary)}</span>
      </div>
      <div className="payroll-result-row">
        <span>ISR retenido</span>
        <span>− {formatCurrency(breakdown.isr_deduction)}</span>
      </div>
      <div className="payroll-result-row">
        <span>IMSS retenido</span>
        <span>− {formatCurrency(breakdown.imss_deduction)}</span>
      </div>
      <div className="payroll-result-row total">
        <span>Neto a pagar</span>
        <span>{formatCurrency(breakdown.net_salary)}</span>
      </div>

      <p className="payroll-result-footer">
        Guardado como recibo #{result.receipt_id}
        {result.employee_name ? ` de ${result.employee_name}` : ""}. Ya es visible en su portal.
      </p>
    </motion.div>
  );
}
