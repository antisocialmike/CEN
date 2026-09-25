import { describe, expect, it } from "vitest";
import { isPeriodPreset, resolvePreset } from "./analyticsPeriods";

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
