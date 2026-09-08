import httpClient from "./httpClient";
import {
  clearPasswordChangeFlag,
  clearSession,
  saveSession,
  UserRole
} from "./authSession";

interface LoginResponse {
  access_token: string;
  role: UserRole;
  name?: string;
  employee_id?: number | null;
  must_change_password?: boolean;
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
    employeeId: response.data.employee_id ?? null,
    mustChangePassword: response.data.must_change_password ?? false
  });

  return response.data.role;
}

export function logout(): void {
  clearSession();
}

export async function changePassword(
  currentPassword: string,
  newPassword: string
): Promise<void> {
  await httpClient.post("/auth/password", {
    current_password: currentPassword,
    new_password: newPassword
  });
  clearPasswordChangeFlag();
}
