import { beforeEach, describe, expect, it } from "vitest";
import {
  clearPasswordChangeFlag,
  clearSession,
  dashboardPathForRole,
  getEmployeeId,
  getInitials,
  getName,
  getRole,
  getRoleLabel,
  getToken,
  isAuthenticated,
  mustChangePassword,
  saveSession
} from "./authSession";

const adminSession = {
  accessToken: "token-abc",
  role: "admin" as const,
  name: "Ana Sofia Ramirez",
  employeeId: 7,
  mustChangePassword: false
};

beforeEach(() => {
  localStorage.clear();
});

describe("saveSession", () => {
  it("guarda y recupera la sesion completa", () => {
    saveSession(adminSession);

    expect(getToken()).toBe("token-abc");
    expect(getRole()).toBe("admin");
    expect(getName()).toBe("Ana Sofia Ramirez");
    expect(getEmployeeId()).toBe(7);
    expect(mustChangePassword()).toBe(false);
  });

  it("guarda la marca de contrasena temporal", () => {
    saveSession({ ...adminSession, mustChangePassword: true });

    expect(mustChangePassword()).toBe(true);
  });
});

describe("isAuthenticated", () => {
  it("es falso sin sesion", () => {
    expect(isAuthenticated()).toBe(false);
  });

  it("es verdadero con token y rol", () => {
    saveSession(adminSession);

    expect(isAuthenticated()).toBe(true);
  });

  it("es falso si el rol guardado no es valido", () => {
    saveSession(adminSession);
    localStorage.setItem("cen_user_role", "superadmin");

    expect(getRole()).toBeNull();
    expect(isAuthenticated()).toBe(false);
  });
});

describe("clearSession", () => {
  it("borra todo, incluida la marca de contrasena", () => {
    saveSession({ ...adminSession, mustChangePassword: true });

    clearSession();

    expect(getToken()).toBeNull();
    expect(getRole()).toBeNull();
    expect(getEmployeeId()).toBeNull();
    expect(mustChangePassword()).toBe(false);
  });
});

describe("clearPasswordChangeFlag", () => {
  it("quita la marca sin tocar el resto de la sesion", () => {
    saveSession({ ...adminSession, mustChangePassword: true });

    clearPasswordChangeFlag();

    expect(mustChangePassword()).toBe(false);
    expect(getToken()).toBe("token-abc");
  });
});

describe("getInitials", () => {
  it("toma la inicial del nombre y del apellido", () => {
    saveSession(adminSession);

    expect(getInitials()).toBe("AS");
  });

  it("usa dos letras cuando solo hay un nombre", () => {
    saveSession({ ...adminSession, name: "Ana" });

    expect(getInitials()).toBe("AN");
  });

  it("cae al rol cuando no hay nombre", () => {
    saveSession({ ...adminSession, name: "" });

    expect(getInitials()).toBe("A");
  });

  it("cae a la E del empleado cuando no hay nombre", () => {
    saveSession({ ...adminSession, name: "", role: "employee" });

    expect(getInitials()).toBe("E");
  });
});

describe("getRoleLabel y dashboardPathForRole", () => {
  it("resuelve al administrador", () => {
    saveSession(adminSession);

    expect(getRoleLabel()).toBe("Administrador");
    expect(dashboardPathForRole()).toBe("/admin");
  });

  it("resuelve al empleado", () => {
    saveSession({ ...adminSession, role: "employee" });

    expect(getRoleLabel()).toBe("Empleado");
    expect(dashboardPathForRole()).toBe("/empleado");
  });
});
