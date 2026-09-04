import httpClient from "./httpClient";
import { saveSession, clearSession, UserRole } from "./authSession";

interface LoginResponse {
  access_token: string;
  role: UserRole;
}

export async function login(email: string, password: string): Promise<UserRole> {
  const response = await httpClient.post<LoginResponse>("/auth/login", {
    email,
    password
  });
  saveSession(response.data.access_token, response.data.role);
  return response.data.role;
}

export function logout(): void {
  clearSession();
}
