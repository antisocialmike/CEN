export type UserRole = "admin" | "employee";

const TOKEN_KEY = "cen_access_token";
const ROLE_KEY = "cen_user_role";
const NAME_KEY = "cen_user_name";
const EMPLOYEE_ID_KEY = "cen_employee_id";

export interface Session {
  accessToken: string;
  role: UserRole;
  name: string;
  employeeId: number | null;
}

export function saveSession(session: Session): void {
  localStorage.setItem(TOKEN_KEY, session.accessToken);
  localStorage.setItem(ROLE_KEY, session.role);
  localStorage.setItem(NAME_KEY, session.name);
  if (session.employeeId !== null) {
    localStorage.setItem(EMPLOYEE_ID_KEY, String(session.employeeId));
  }
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getRole(): UserRole | null {
  const role = localStorage.getItem(ROLE_KEY);
  return role === "admin" || role === "employee" ? role : null;
}

export function getName(): string {
  return localStorage.getItem(NAME_KEY) ?? "";
}

export function getEmployeeId(): number | null {
  const raw = localStorage.getItem(EMPLOYEE_ID_KEY);
  return raw === null ? null : Number(raw);
}

export function clearSession(): void {
  [TOKEN_KEY, ROLE_KEY, NAME_KEY, EMPLOYEE_ID_KEY].forEach((key) =>
    localStorage.removeItem(key)
  );
}

export function isAuthenticated(): boolean {
  return getToken() !== null && getRole() !== null;
}

export function getInitials(): string {
  const parts = getName().trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) {
    return getRole() === "admin" ? "A" : "E";
  }
  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase();
  }
  return (parts[0][0] + parts[1][0]).toUpperCase();
}

export function getRoleLabel(): string {
  return getRole() === "admin" ? "Administrador" : "Empleado";
}
