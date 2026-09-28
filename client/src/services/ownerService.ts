import httpClient from "./httpClient";
import { companyPayload, CompanyInput, EntidadFederativa } from "./companyData";
import { Periodicity } from "./payrollService";

// La API analitica manda los importes como texto para no perder centavos en el
// camino. Se leen con toAmount justo antes de pintarlos o graficarlos.
export type Amount = string;

export function toAmount(value: Amount | null): number {
  return value === null ? 0 : Number(value);
}

export interface CompanyAdmin {
  id: number;
  name: string;
  email: string;
  is_active: boolean;
  assigned_at: string;
}

export interface RiskPremium {
  rate: Amount;
  valid_from: string;
}

export interface OwnerCompany {
  id: number;
  legal_name: string;
  trade_name: string | null;
  rfc: string | null;
  registro_patronal: string | null;
  entidad_federativa: EntidadFederativa | null;
  is_active: boolean;
  created_at: string;
  active_employees: number;
  risk_premium: RiskPremium | null;
  admins: CompanyAdmin[];
}

export interface AdminInvited {
  company: OwnerCompany;
  admin_id: number;
  temporary_password: string;
}

export interface KpiChange {
  gross_payroll: Amount | null;
  net_paid: Amount | null;
  isr_withheld: Amount | null;
  imss_withheld: Amount | null;
  paid_employees: Amount | null;
  average_cost_per_employee: Amount | null;
  employer_cost: Amount | null;
  total_cost: Amount | null;
}

export interface Kpis {
  gross_payroll: Amount;
  net_paid: Amount;
  isr_withheld: Amount;
  imss_withheld: Amount;
  total_deductions: Amount;
  receipts: number;
  paid_employees: number;
  active_employees: number;
  average_cost_per_employee: Amount | null;
  employer_cost: Amount;
  total_cost: Amount;
  employer_cost_pct: Amount | null;
  change: KpiChange;
}

export interface MonthlyPayroll {
  month: string;
  gross_payroll: Amount;
  net_paid: Amount;
  isr_withheld: Amount;
  imss_withheld: Amount;
  total_deductions: Amount;
  receipts: number;
}

export interface ConceptTotal {
  kind: "perception" | "deduction";
  concept: string;
  description: string;
  amount: Amount;
  taxable: Amount;
  exempt: Amount;
}

export interface HeadcountMonth {
  month: string;
  hires: number;
  terminations: number;
}

export interface TopSalary {
  id: number;
  name: string;
  company_name: string;
  base_salary: Amount;
}

export interface SalaryBucket {
  label: string;
  min_salary: Amount;
  max_salary: Amount | null;
  employees: number;
}

export interface CompanyComparison {
  id: number;
  legal_name: string;
  is_active: boolean;
  gross_payroll: Amount;
  net_paid: Amount;
  employer_cost: Amount;
  // Nomina bruta mas costo patronal, como total_cost en los KPI.
  total_cost: Amount;
  receipts: number;
  paid_employees: number;
  active_employees: number;
}

export type EmployerCostGroup = "imss" | "sar" | "infonavit" | "isn";

export interface EmployerCostComponent {
  group_key: EmployerCostGroup;
  component: string;
  description: string;
  amount: Amount;
}

export interface EmployerCostMonth {
  month: string;
  imss: Amount;
  sar: Amount;
  infonavit: Amount;
  isn: Amount;
  covered_gross: Amount;
}

export interface EmployerCost {
  coverage: {
    receipts_with_cost: number;
    receipts_incomplete: number;
    receipts_without_cost: number;
  };
  components: EmployerCostComponent[];
  missing: { name: string; receipts: number }[];
  monthly: EmployerCostMonth[];
}

export interface PayrollAnalytics {
  company_id: number | null;
  period: {
    start: string;
    end: string;
    previous_start: string;
    previous_end: string;
    periodicity: Periodicity | null;
  };
  kpis: Kpis;
  monthly: MonthlyPayroll[];
  concepts: ConceptTotal[];
  headcount: { active: number; inactive: number; by_month: HeadcountMonth[] };
  top_salaries: TopSalary[];
  salary_histogram: SalaryBucket[];
  companies: CompanyComparison[];
  employer_cost: EmployerCost;
}

export interface AnalyticsQuery {
  companyId: number | "all";
  from: string;
  to: string;
}

export async function listOwnerCompanies(): Promise<OwnerCompany[]> {
  const response = await httpClient.get<OwnerCompany[]>("/owner/companies");
  return response.data;
}

export async function getAnalytics(query: AnalyticsQuery): Promise<PayrollAnalytics> {
  const response = await httpClient.get<PayrollAnalytics>("/owner/analytics", {
    params: { company_id: query.companyId, from: query.from, to: query.to }
  });
  return response.data;
}

export async function updateOwnerCompany(id: number, input: CompanyInput): Promise<OwnerCompany> {
  const response = await httpClient.put<OwnerCompany>(
    `/owner/companies/${id}`,
    companyPayload(input)
  );
  return response.data;
}

export async function setOwnerCompanyActive(id: number, isActive: boolean): Promise<OwnerCompany> {
  const action = isActive ? "activate" : "deactivate";
  const response = await httpClient.post<OwnerCompany>(`/owner/companies/${id}/${action}`);
  return response.data;
}

export async function setRiskPremium(
  companyId: number,
  input: { ratePercent: string; validFrom: string }
): Promise<OwnerCompany> {
  const response = await httpClient.put<OwnerCompany>(
    `/owner/companies/${companyId}/risk-premium`,
    { rate_percent: input.ratePercent, valid_from: input.validFrom }
  );
  return response.data;
}

export async function inviteAdmin(
  companyId: number,
  input: { name: string; email: string }
): Promise<AdminInvited> {
  const response = await httpClient.post<AdminInvited>(
    `/owner/companies/${companyId}/admins/invite`,
    input
  );
  return response.data;
}

export async function assignAdmin(companyId: number, email: string): Promise<OwnerCompany> {
  const response = await httpClient.post<OwnerCompany>(`/owner/companies/${companyId}/admins`, {
    email
  });
  return response.data;
}

export async function unassignAdmin(companyId: number, adminId: number): Promise<OwnerCompany> {
  const response = await httpClient.delete<OwnerCompany>(
    `/owner/companies/${companyId}/admins/${adminId}`
  );
  return response.data;
}
