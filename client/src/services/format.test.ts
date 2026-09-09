import { afterEach, describe, expect, it, vi } from "vitest";
import {
  currentPeriod,
  formatCurrency,
  formatDate,
  formatDateShort,
  formatMonth,
  formatRange,
  periodStartsOf
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

describe("formatRange", () => {
  it("no repite el mes cuando el periodo cae dentro de uno solo", () => {
    expect(formatRange("2026-09-01", "2026-09-15")).toBe(
      "1 al 15 de septiembre de 2026"
    );
  });

  it("nombra los dos meses cuando el periodo los cruza", () => {
    expect(formatRange("2026-09-28", "2026-10-04")).toBe(
      "28 de septiembre de 2026 al 4 de octubre de 2026"
    );
  });
});

describe("periodStartsOf", () => {
  it("da un solo inicio para el mensual", () => {
    expect(periodStartsOf("mensual", "2026-09")).toEqual(["2026-09-01"]);
  });

  it("da las dos quincenas", () => {
    expect(periodStartsOf("quincenal", "2026-09")).toEqual([
      "2026-09-01",
      "2026-09-16"
    ]);
  });

  it("da las semanas del mes", () => {
    expect(periodStartsOf("semanal", "2026-09")).toEqual([
      "2026-09-01",
      "2026-09-08",
      "2026-09-15",
      "2026-09-22",
      "2026-09-29"
    ]);
  });

  it("respeta un febrero mas corto", () => {
    expect(periodStartsOf("semanal", "2026-02")).toHaveLength(4);
  });
});
