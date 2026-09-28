import { describe, expect, it, vi } from "vitest";
import httpClient from "./httpClient";
import { createEmployee, isOnPayroll, updateEmployee } from "./employeeService";

vi.mock("./httpClient", () => ({
  default: { post: vi.fn(async () => ({ data: {} })), put: vi.fn(async () => ({ data: {} })) }
}));

const base = {
  id: 1,
  name: "Ana",
  email: "ana@cen.com",
  role: "employee" as const,
  tipo_regimen: "02" as const,
  tipo_jornada: "01" as const
};

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

describe("fecha de ingreso hacia la API", () => {
  it("el alta la manda como hire_date", async () => {
    await createEmployee({
      name: "Ana",
      email: "ana@cen.com",
      role: "employee",
      baseSalary: 18000,
      password: "clave1234",
      tipoRegimen: "02",
      tipoJornada: "01",
      hireDate: "2019-06-03"
    });

    expect(httpClient.post).toHaveBeenCalledWith(
      "/employees",
      expect.objectContaining({ hire_date: "2019-06-03" })
    );
  });

  it("la edicion manda null para conservar la que ya tiene", async () => {
    await updateEmployee(3, {
      name: "Ana",
      email: "ana@cen.com",
      role: "employee",
      baseSalary: 18000,
      tipoRegimen: "02",
      tipoJornada: "01",
      hireDate: null
    });

    expect(httpClient.put).toHaveBeenCalledWith(
      "/employees/3",
      expect.objectContaining({ hire_date: null })
    );
  });
});
