import { describe, expect, it } from "vitest";
import { isPeriodPreset, resolvePreset, withoutEmptyCurrentMonth } from "./analyticsPeriods";
import type { PayrollAnalytics } from "./ownerService";

function analyticsWith(receipts: number[]): PayrollAnalytics {
  const months = ["2026-08-01", "2026-09-01", "2026-10-01"].slice(-receipts.length);
  return {
    monthly: months.map((month, index) => ({ month, receipts: receipts[index] })),
    employer_cost: { monthly: months.map((month) => ({ month })) }
  } as unknown as PayrollAnalytics;
}

describe("withoutEmptyCurrentMonth", () => {
  const october = new Date(2026, 9, 1);

  it("quita el mes en curso de las gráficas mientras no tenga recibos", () => {
    const result = withoutEmptyCurrentMonth(analyticsWith([40, 40, 0]), october);

    expect(result.monthly.map((month) => month.month)).toEqual(["2026-08-01", "2026-09-01"]);
    expect(result.employer_cost.monthly.map((month) => month.month)).toEqual([
      "2026-08-01",
      "2026-09-01"
    ]);
  });

  it("deja el mes en curso en cuanto tiene un recibo", () => {
    const analytics = analyticsWith([40, 40, 1]);

    expect(withoutEmptyCurrentMonth(analytics, october)).toBe(analytics);
  });

  it("deja en cero un mes pasado sin recibos", () => {
    const analytics = analyticsWith([40, 0, 0]);

    expect(withoutEmptyCurrentMonth(analytics, new Date(2026, 10, 3))).toBe(analytics);
  });

  it("no deja vacía la gráfica de este mes", () => {
    const analytics = analyticsWith([0]);

    expect(withoutEmptyCurrentMonth(analytics, october)).toBe(analytics);
  });
});

const today = new Date(2026, 7, 20); // 20 de agosto de 2026

describe("resolvePreset", () => {
  it.each([
    ["mes", "2026-08-01"],
    ["trimestre", "2026-07-01"],
    ["anio", "2026-01-01"],
    ["12m", "2025-09-01"]
  ] as const)("%s empieza el %s y termina hoy", (preset, from) => {
    expect(resolvePreset(preset, today)).toEqual({ from, to: "2026-08-20" });
  });

  it("el trimestre de enero empieza en enero", () => {
    expect(resolvePreset("trimestre", new Date(2026, 0, 5)).from).toBe("2026-01-01");
  });
});

describe("isPeriodPreset", () => {
  it("solo acepta los presets conocidos", () => {
    expect(isPeriodPreset("anio")).toBe(true);
    expect(isPeriodPreset("siempre")).toBe(false);
    expect(isPeriodPreset(null)).toBe(false);
  });
});
