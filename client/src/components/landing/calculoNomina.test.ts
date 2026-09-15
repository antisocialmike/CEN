import { describe, expect, it } from "vitest";
import { calcularIMSS, calcularISR, desglosar } from "./calculoNomina";

const REFERENCIA_SERVIDOR = [
  { periodicidad: "mensual", bruto: 22000, isr: 2810.85, imss: 567.71, neto: 18621.44 },
  { periodicidad: "mensual", bruto: 12000, isr: 946.62, imss: 290.21, neto: 10763.17 },
  { periodicidad: "mensual", bruto: 8000, isr: 0.0, imss: 190.0, neto: 7810.0 },
  { periodicidad: "mensual", bruto: 35000, isr: 5587.65, imss: 928.46, neto: 28483.89 },
  { periodicidad: "quincenal", bruto: 22000, isr: 3848.31, imss: 589.1, neto: 17562.59 },
  { periodicidad: "quincenal", bruto: 12000, isr: 1619.03, imss: 311.6, neto: 10069.37 },
  { periodicidad: "quincenal", bruto: 8000, isr: 791.01, imss: 200.6, neto: 7008.39 },
  { periodicidad: "quincenal", bruto: 35000, isr: 7368.04, imss: 949.85, neto: 26682.11 }
] as const;

describe("calculoNomina no puede separarse del servidor", () => {
  it.each(REFERENCIA_SERVIDOR)(
    "$periodicidad $bruto coincide con el calculo del servidor",
    ({ periodicidad, bruto, isr, imss, neto }) => {
      expect(calcularISR(bruto, periodicidad)).toBeCloseTo(isr, 2);
      expect(calcularIMSS(bruto, periodicidad)).toBeCloseTo(imss, 2);

      const d = desglosar(bruto, periodicidad);
      expect(d.neto).toBeCloseTo(neto, 2);
      expect(d.bruto + 0).toBeCloseTo(bruto, 2);
    }
  );

  it("el subsidio al empleo lleva el ISR a cero en sueldos bajos", () => {
    expect(calcularISR(8000, "mensual")).toBe(0);
    expect(calcularISR(12000, "mensual")).toBeGreaterThan(0);
  });

  it("el IMSS topa a 25 UMA y deja de crecer", () => {
    const tope = 3566.22 * 25;
    expect(calcularIMSS(tope, "mensual")).toBeCloseTo(calcularIMSS(tope * 3, "mensual"), 2);
  });

  it("un bruto invalido no rompe el desglose", () => {
    for (const malo of [0, -5000, Number.NaN, Number.POSITIVE_INFINITY]) {
      const d = desglosar(malo, "mensual");
      expect(d.bruto).toBe(0);
      expect(d.isr).toBe(0);
      expect(d.neto).toBe(0);
    }
  });

  it("el neto siempre cuadra con bruto menos retenciones", () => {
    for (const bruto of [5000, 9500, 15000, 22000, 48000, 120000]) {
      const d = desglosar(bruto, "mensual");
      expect(d.neto).toBeCloseTo(d.bruto - d.isr - d.imss, 2);
    }
  });
});
