import httpClient from "./httpClient";
import { UserRole } from "./authSession";

export interface NewEmployeeInput {
  name: string;
  email: string;
  role: UserRole;
  baseSalary: number;
  password: string;
}

export interface EmployeeCreated {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  base_salary: number;
  is_active: boolean;
}

export interface EmployeeUpdateInput {
  name: string;
  email: string;
  role: UserRole;
  baseSalary: number;
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
