export type UserRole = "superadmin" | "owner" | "admin" | "employee";
export type EmployeeRole = Extract<UserRole, "admin" | "employee">;

const USER_ROLES: readonly UserRole[] = ["superadmin", "owner", "admin", "employee"];

const DASHBOARD_PATHS: Record<UserRole, string> = {
  superadmin: "/superadmin",
  owner: "/dueno",
  admin: "/admin",
  employee: "/empleado"
};

const ROLE_LABELS: Record<UserRole, string> = {
  superadmin: "Superadministrador",
  owner: "Dueño",
  admin: "Administrador",
  employee: "Empleado"
};

const TOKEN_KEY = "cen_access_token";
const ROLE_KEY = "cen_user_role";
const NAME_KEY = "cen_user_name";
const EMPLOYEE_ID_KEY = "cen_employee_id";
const MUST_CHANGE_KEY = "cen_must_change_password";

export interface Session {
  accessToken: string;
  role: UserRole;
  name: string;
  employeeId: number | null;
  mustChangePassword: boolean;
}

export function saveSession(session: Session): void {
  localStorage.setItem(TOKEN_KEY, session.accessToken);
  localStorage.setItem(ROLE_KEY, session.role);
  localStorage.setItem(NAME_KEY, session.name);
  if (session.employeeId !== null) {
    localStorage.setItem(EMPLOYEE_ID_KEY, String(session.employeeId));
  }
  localStorage.setItem(MUST_CHANGE_KEY, String(session.mustChangePassword));
}

export function mustChangePassword(): boolean {
  return localStorage.getItem(MUST_CHANGE_KEY) === "true";
}

export function clearPasswordChangeFlag(): void {
  localStorage.setItem(MUST_CHANGE_KEY, "false");
}

export function dashboardPathForRole(role: UserRole | null = getRole()): string {
  return DASHBOARD_PATHS[role ?? "employee"];
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getRole(): UserRole | null {
  const role = localStorage.getItem(ROLE_KEY);
  return USER_ROLES.find((known) => known === role) ?? null;
}

export function getName(): string {
  return localStorage.getItem(NAME_KEY) ?? "";
}

export function getEmployeeId(): number | null {
  const raw = localStorage.getItem(EMPLOYEE_ID_KEY);
  return raw === null ? null : Number(raw);
}

export function clearSession(): void {
  [TOKEN_KEY, ROLE_KEY, NAME_KEY, EMPLOYEE_ID_KEY, MUST_CHANGE_KEY].forEach((key) =>
    localStorage.removeItem(key)
  );
}

function decodeExpiry(token: string): number | null {
  try {
    const payload = token.split(".")[1];
    if (!payload) return null;

    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(
      normalized.length + ((4 - (normalized.length % 4)) % 4),
      "="
    );
    const claims = JSON.parse(atob(padded)) as { exp?: unknown };
    return typeof claims.exp === "number" ? claims.exp * 1000 : null;
  } catch {
    return null;
  }
}

export function isTokenExpired(token: string): boolean {
  const expiresAt = decodeExpiry(token);
  return expiresAt !== null && expiresAt <= Date.now();
}

export function isAuthenticated(): boolean {
  const token = getToken();
  if (token === null || getRole() === null) {
    return false;
  }

  if (isTokenExpired(token)) {
    clearSession();
    return false;
  }

  return true;
}

export function getInitials(): string {
  const parts = getName().trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) {
    return getRoleLabel().charAt(0);
  }
  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase();
  }
  return (parts[0][0] + parts[1][0]).toUpperCase();
}

export function getRoleLabel(): string {
  return ROLE_LABELS[getRole() ?? "employee"];
}
