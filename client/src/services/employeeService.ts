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
