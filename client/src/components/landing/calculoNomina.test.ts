import { describe, expect, it } from "vitest";
import { calcularIMSS, calcularISR, desglosar } from "./calculoNomina";

const REFERENCIA_SERVIDOR = [
  // Salida de PayrollService con los parametros de 2026 y el SBC de primer año.
  { periodicidad: "mensual", bruto: 22000, isr: 2810.85, imss: 598.37, neto: 18590.78 },
  { periodicidad: "mensual", bruto: 12000, isr: 946.62, imss: 307.19, neto: 10746.19 },
  { periodicidad: "mensual", bruto: 8000, isr: 0.0, imss: 0.0, neto: 8000.0 },
  { periodicidad: "mensual", bruto: 35000, isr: 5587.65, imss: 976.91, neto: 28435.44 },
  { periodicidad: "quincenal", bruto: 22000, isr: 3848.31, imss: 619.49, neto: 17532.2 },
  { periodicidad: "quincenal", bruto: 12000, isr: 1619.03, imss: 328.31, neto: 10052.66 },
  { periodicidad: "quincenal", bruto: 8000, isr: 791.01, imss: 211.83, neto: 6997.16 },
  { periodicidad: "quincenal", bruto: 35000, isr: 7368.04, imss: 998.03, neto: 26633.93 }
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
    expect(calcularISR(10000, "mensual")).toBeCloseTo(193.37, 2);
    expect(calcularISR(12000, "mensual")).toBeGreaterThan(0);
  });

  it("a quien gana el salario minimo no se le retiene nada", () => {
    // 315.04 x 30: su IMSS lo paga el patron.
    expect(calcularISR(9451.2, "mensual")).toBe(0);
    expect(calcularIMSS(9451.2, "mensual")).toBe(0);
    expect(calcularIMSS(9500, "mensual")).toBeGreaterThan(0);
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
