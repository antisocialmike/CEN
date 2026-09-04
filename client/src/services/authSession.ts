export type UserRole = "admin" | "employee";

const TOKEN_KEY = "cen_access_token";
const ROLE_KEY = "cen_user_role";

export function saveSession(accessToken: string, role: UserRole): void {
  localStorage.setItem(TOKEN_KEY, accessToken);
  localStorage.setItem(ROLE_KEY, role);
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getRole(): UserRole | null {
  const role = localStorage.getItem(ROLE_KEY);
  return role === "admin" || role === "employee" ? role : null;
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
}

export function isAuthenticated(): boolean {
  return getToken() !== null && getRole() !== null;
}
