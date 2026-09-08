import { afterEach, describe, expect, it, vi } from "vitest";
import {
  currentPeriod,
  formatCurrency,
  formatDate,
  formatDateShort,
  formatMonth
} from "./format";

afterEach(() => {
  vi.useRealTimers();
});

describe("formatCurrency", () => {
  it("da formato de pesos mexicanos con dos decimales", () => {
    expect(formatCurrency(15586.8)).toContain("15,586.80");
  });

  it("soporta el cero", () => {
    expect(formatCurrency(0)).toContain("0.00");
  });
});

describe("formatMonth", () => {
  it("no adelanta ni atrasa el mes por la zona horaria", () => {
    expect(formatMonth("2026-09-01")).toBe("Septiembre de 2026");
  });

  it("respeta el mes en el primer dia de enero", () => {
    expect(formatMonth("2026-01-01")).toBe("Enero de 2026");
  });

  it("sigue funcionando con una fecha con hora", () => {
    expect(formatMonth("2026-09-15T10:00:00")).toBe("Septiembre de 2026");
  });
});

describe("formatDate", () => {
  it("mantiene el dia exacto de una fecha sin hora", () => {
    expect(formatDate("2026-09-01")).toBe("1 de septiembre de 2026");
  });
});

describe("formatDateShort", () => {
  it("devuelve dia y mes abreviado", () => {
    expect(formatDateShort("2026-09-01")).toMatch(/01/);
  });
});

describe("currentPeriod", () => {
  it("devuelve el mes actual en formato AAAA-MM", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 8, 8));
    expect(currentPeriod()).toBe("2026-09");
  });

  it("rellena con cero los meses de un digito", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 0, 31));
    expect(currentPeriod()).toBe("2026-01");
  });
});
