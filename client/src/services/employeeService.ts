import httpClient from "./httpClient";
import { EmployeeRole } from "./authSession";
import { Pagina, POR_PAGINA } from "./pagina";

// Claves del SAT (c_TipoRegimen y c_TipoJornada), las mismas que guarda la API.
export type TipoRegimen = "02" | "09";
export type TipoJornada = "01" | "02" | "03";

export const TIPO_REGIMEN_LABELS: Record<TipoRegimen, string> = {
  "02": "Sueldos y salarios",
  "09": "Asimilados a salarios (honorarios)"
};

export const TIPO_JORNADA_LABELS: Record<TipoJornada, string> = {
  "01": "Diurna (8 horas)",
  "02": "Nocturna (7 horas)",
  "03": "Mixta (7.5 horas)"
};

export interface NewEmployeeInput {
  name: string;
  email: string;
  role: EmployeeRole;
  baseSalary: number;
  password: string;
  tipoRegimen: TipoRegimen;
  tipoJornada: TipoJornada;
  hireDate: string;
  rfc: string;
  curp: string;
  nss: string;
}

export interface EmployeeCreated {
  id: number;
  name: string;
  email: string;
  role: EmployeeRole;
  // Vacío para los administradores que invita un dueño: operan la nómina, no la cobran.
  base_salary: number | null;
  is_active: boolean;
  tipo_regimen: TipoRegimen;
  tipo_jornada: TipoJornada;
  hire_date?: string | null;
  rfc?: string | null;
  curp?: string | null;
  nss?: string | null;
  linked?: boolean;
}

export function missingFiscalData(employee: EmployeeCreated): boolean {
  return !employee.rfc || !employee.curp || (!isAssimilated(employee) && !employee.nss);
}

export interface SalaryChange {
  base_salary: number;
  valid_from: string;
  recorded_at: string;
  recorded_by: string | null;
}

// Sin relacion laboral: no cotiza al IMSS ni tiene prestaciones de la LFT.
export function isAssimilated(employee: Pick<EmployeeCreated, "tipo_regimen">): boolean {
  return employee.tipo_regimen === "09";
}

export type PayrollEmployee = EmployeeCreated & { base_salary: number };

export function isOnPayroll(employee: EmployeeCreated): employee is PayrollEmployee {
  return employee.is_active && employee.base_salary !== null;
}

export interface EmployeeUpdateInput {
  name: string;
  email: string;
  role: EmployeeRole;
  baseSalary: number | null;
  tipoRegimen: TipoRegimen;
  tipoJornada: TipoJornada;
  hireDate: string | null;
  rfc: string;
  curp: string;
  nss: string;
  salaryValidFrom: string | null;
}

export async function createEmployee(input: NewEmployeeInput): Promise<EmployeeCreated> {
  const response = await httpClient.post<EmployeeCreated>("/employees", {
    name: input.name,
    email: input.email,
    role: input.role,
    base_salary: input.baseSalary,
    password: input.password,
    tipo_regimen: input.tipoRegimen,
    tipo_jornada: input.tipoJornada,
    hire_date: input.hireDate,
    rfc: input.rfc || null,
    curp: input.curp || null,
    nss: input.nss || null
  });
  return response.data;
}

export async function listEmployees(): Promise<EmployeeCreated[]> {
  const response = await httpClient.get<EmployeeCreated[]>("/employees");
  return response.data;
}

export async function listEmployeesPage(pagina: number): Promise<Pagina<EmployeeCreated>> {
  const response = await httpClient.get<Pagina<EmployeeCreated>>("/employees", {
    params: { page: pagina, page_size: POR_PAGINA }
  });
  return response.data;
}

export async function updateEmployee(
  id: number,
  input: EmployeeUpdateInput
): Promise<EmployeeCreated> {
  const response = await httpClient.put<EmployeeCreated>(`/employees/${id}`, {
    name: input.name,
    email: input.email,
    role: input.role,
    base_salary: input.baseSalary,
    tipo_regimen: input.tipoRegimen,
    tipo_jornada: input.tipoJornada,
    hire_date: input.hireDate,
    rfc: input.rfc || null,
    curp: input.curp || null,
    nss: input.nss || null,
    salary_valid_from: input.salaryValidFrom
  });
  return response.data;
}

export async function getSalaryHistory(id: number): Promise<SalaryChange[]> {
  const response = await httpClient.get<SalaryChange[]>(`/employees/${id}/salary-history`);
  return response.data;
}

export async function deactivateEmployee(id: number): Promise<EmployeeCreated> {
  const response = await httpClient.post<EmployeeCreated>(`/employees/${id}/deactivate`);
  return response.data;
}

export async function activateEmployee(id: number): Promise<EmployeeCreated> {
  const response = await httpClient.post<EmployeeCreated>(`/employees/${id}/activate`);
  return response.data;
}

export interface PasswordReset {
  employee_id: number;
  name: string;
  email: string;
  temporary_password: string;
}

export async function resetEmployeePassword(id: number): Promise<PasswordReset> {
  const response = await httpClient.post<PasswordReset>(
    `/employees/${id}/reset-password`
  );
  return response.data;
}
