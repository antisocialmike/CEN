import { describe, expect, it } from "vitest";
import { isOnPayroll } from "./employeeService";

const base = { id: 1, name: "Ana", email: "ana@cen.com", role: "employee" as const };

describe("isOnPayroll", () => {
  it("incluye a quien está activo y tiene salario", () => {
    expect(isOnPayroll({ ...base, base_salary: 18000, is_active: true })).toBe(true);
  });

  it("deja fuera a quien está dado de baja", () => {
    expect(isOnPayroll({ ...base, base_salary: 18000, is_active: false })).toBe(false);
  });

  it("deja fuera a los administradores que no cobran nómina", () => {
    expect(isOnPayroll({ ...base, role: "admin", base_salary: null, is_active: true })).toBe(false);
  });
});
