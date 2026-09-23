import httpClient from "./httpClient";
import { EmployeeRole } from "./authSession";

export interface NewEmployeeInput {
  name: string;
  email: string;
  role: EmployeeRole;
  baseSalary: number;
  password: string;
}

export interface EmployeeCreated {
  id: number;
  name: string;
  email: string;
  role: EmployeeRole;
  // Vacío para los administradores que invita un dueño: operan la nómina, no la cobran.
  base_salary: number | null;
  is_active: boolean;
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
}

export async function createEmployee(input: NewEmployeeInput): Promise<EmployeeCreated> {
  const response = await httpClient.post<EmployeeCreated>("/employees", {
    name: input.name,
    email: input.email,
    role: input.role,
    base_salary: input.baseSalary,
    password: input.password
  });
  return response.data;
}

export async function listEmployees(): Promise<EmployeeCreated[]> {
  const response = await httpClient.get<EmployeeCreated[]>("/employees");
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
    base_salary: input.baseSalary
  });
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
