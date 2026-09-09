import { PayrollItem } from "../services/payrollService";
import { formatCurrency } from "../services/format";

interface PayrollBreakdownRowsProps {
  items: PayrollItem[];
  totalPerceptions: number;
  totalDeductions: number;
}

export default function PayrollBreakdownRows({
  items,
  totalPerceptions,
  totalDeductions
}: PayrollBreakdownRowsProps) {
  const perceptions = items.filter((item) => item.kind === "perception");
  const deductions = items.filter((item) => item.kind === "deduction");

  return (
    <>
      <div className="payroll-result-row is-group">
        <span>Percepciones</span>
        <span>{formatCurrency(totalPerceptions)}</span>
      </div>
      {perceptions.map((item) => (
        <div className="payroll-result-row is-item" key={item.concept}>
          <span>{item.description}</span>
          <span>{formatCurrency(item.amount)}</span>
        </div>
      ))}

      <div className="payroll-result-row is-group">
        <span>Deducciones</span>
        <span>− {formatCurrency(totalDeductions)}</span>
      </div>
      {deductions.map((item) => (
        <div className="payroll-result-row is-item" key={item.concept}>
          <span>{item.description}</span>
          <span>− {formatCurrency(item.amount)}</span>
        </div>
      ))}
    </>
  );
}
