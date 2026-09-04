import httpClient from "./httpClient";

export interface PayrollBreakdown {
  gross_salary: number;
  isr_deduction: number;
  imss_deduction: number;
  net_salary: number;
}

export interface PayrollCalculationResult {
  receipt_id: number;
  employee_id: number;
  data: PayrollBreakdown;
  processed_by: string;
}

export interface PayrollReceipt {
  id: number;
  employee_id: number;
  gross_salary: number;
  isr_deduction: number;
  imss_deduction: number;
  net_salary: number;
  created_at: string;
}

export async function calculatePayroll(
  employeeId: number,
  grossSalary: number
): Promise<PayrollCalculationResult> {
  const response = await httpClient.post<PayrollCalculationResult>("/payroll/calculate", {
    employee_id: employeeId,
    gross_salary: grossSalary
  });
  return response.data;
}

export async function getMyReceipts(): Promise<PayrollReceipt[]> {
  const response = await httpClient.get<{ employee_id: number; receipts: PayrollReceipt[] }>(
    "/payroll/my-receipts"
  );
  return response.data.receipts;
}
