import httpClient from "./httpClient";

export interface PayrollBreakdown {
  gross_salary: number;
  isr_deduction: number;
  imss_deduction: number;
  net_salary: number;
}

export interface PayrollCalculationResult {
  receipt_id: number;
  created: boolean;
  employee_id: number;
  employee_name?: string;
  period: string;
  data: PayrollBreakdown;
  processed_by: string;
}

export interface PayrollReceipt {
  id: number;
  employee_id: number;
  employee_name?: string;
  period: string;
  gross_salary: number;
  isr_deduction: number;
  imss_deduction: number;
  net_salary: number;
  processed_by: string;
  created_at: string;
  updated_at?: string;
}

export async function calculatePayroll(
  employeeId: number,
  period: string,
  grossSalary: number
): Promise<PayrollCalculationResult> {
  const response = await httpClient.post<PayrollCalculationResult>("/payroll/calculate", {
    employee_id: employeeId,
    period,
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
