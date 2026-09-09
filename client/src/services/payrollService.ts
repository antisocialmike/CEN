import httpClient from "./httpClient";

export type Periodicity = "mensual" | "quincenal" | "semanal";

export const PERIODICITY_LABELS: Record<Periodicity, string> = {
  mensual: "Mensual",
  quincenal: "Quincenal",
  semanal: "Semanal"
};

export function suggestedGrossSalary(
  baseSalary: number,
  periodicity: Periodicity
): number {
  if (periodicity === "quincenal") return Math.round(baseSalary * 50) / 100;
  if (periodicity === "semanal") {
    return Math.round((baseSalary * 12 * 100) / 52) / 100;
  }
  return baseSalary;
}

export function countActiveConcepts(concepts: PayrollConcepts): number {
  return Object.values(concepts).filter((value) => Number(value) > 0).length;
}

export interface PayrollItem {
  kind: "perception" | "deduction";
  concept: string;
  description: string;
  amount: number;
  taxable: number;
  exempt: number;
}

export interface PayrollBreakdown {
  gross_salary: number;
  isr_deduction: number;
  imss_deduction: number;
  net_salary: number;
  total_perceptions: number;
  total_deductions: number;
  taxable_base: number;
  items: PayrollItem[];
}

export interface PayrollConcepts {
  overtimeDoubleHours: number;
  overtimeTripleHours: number;
  christmasBonusDays: number;
  vacationDays: number;
  bonus: number;
  loanDeduction: number;
  housingCreditDeduction: number;
}

export const emptyConcepts: PayrollConcepts = {
  overtimeDoubleHours: 0,
  overtimeTripleHours: 0,
  christmasBonusDays: 0,
  vacationDays: 0,
  bonus: 0,
  loanDeduction: 0,
  housingCreditDeduction: 0
};

export interface PayrollCalculationResult {
  receipt_id: number;
  created: boolean;
  employee_id: number;
  employee_name?: string;
  period_start: string;
  period_end: string;
  data: PayrollBreakdown;
  processed_by: string;
}

export interface PayrollReceipt {
  id: number;
  employee_id: number;
  employee_name?: string;
  period_start: string;
  period_end: string;
  periodicity: Periodicity;
  paid_days: number;
  gross_salary: number;
  isr_deduction: number;
  imss_deduction: number;
  net_salary: number;
  total_perceptions: number;
  total_deductions: number;
  taxable_base: number;
  items: PayrollItem[];
  processed_by: string;
  created_at: string;
  updated_at?: string;
}

export async function calculatePayroll(
  employeeId: number,
  periodicity: Periodicity,
  periodStart: string,
  grossSalary: number,
  concepts: PayrollConcepts = emptyConcepts
): Promise<PayrollCalculationResult> {
  const response = await httpClient.post<PayrollCalculationResult>("/payroll/calculate", {
    employee_id: employeeId,
    periodicity,
    period_start: periodStart,
    gross_salary: grossSalary,
    overtime_double_hours: concepts.overtimeDoubleHours,
    overtime_triple_hours: concepts.overtimeTripleHours,
    christmas_bonus_days: concepts.christmasBonusDays,
    vacation_days: concepts.vacationDays,
    bonus: concepts.bonus,
    loan_deduction: concepts.loanDeduction,
    housing_credit_deduction: concepts.housingCreditDeduction
  });
  return response.data;
}

export async function getMyReceipts(): Promise<PayrollReceipt[]> {
  const response = await httpClient.get<{ employee_id: number; receipts: PayrollReceipt[] }>(
    "/payroll/my-receipts"
  );
  return response.data.receipts;
}

export async function getRecentReceipts(): Promise<PayrollReceipt[]> {
  const response = await httpClient.get<{ receipts: PayrollReceipt[] }>("/payroll/receipts");
  return response.data.receipts;
}

function filenameFromHeaders(disposition: unknown, fallback: string): string {
  if (typeof disposition !== "string") return fallback;
  const match = disposition.match(/filename="?([^";]+)"?/);
  return match ? match[1] : fallback;
}

export async function downloadReceipt(receiptId: number): Promise<void> {
  const response = await httpClient.get<Blob>(
    `/payroll/receipts/${receiptId}/pdf`,
    { responseType: "blob" }
  );

  const url = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = filenameFromHeaders(
    response.headers["content-disposition"],
    `recibo-${receiptId}.pdf`
  );

  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
