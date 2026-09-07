import httpClient from "./httpClient";
import { saveSession, clearSession, UserRole } from "./authSession";

interface LoginResponse {
  access_token: string;
  role: UserRole;
  name?: string;
  employee_id?: number | null;
}

export async function login(email: string, password: string): Promise<UserRole> {
  const response = await httpClient.post<LoginResponse>("/auth/login", {
    email,
    password
  });

  saveSession({
    accessToken: response.data.access_token,
    role: response.data.role,
    name: response.data.name ?? "",
    employeeId: response.data.employee_id ?? null
  });

  return response.data.role;
}

export function logout(): void {
  clearSession();
}
