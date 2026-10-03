import { describe, expect, it } from "vitest";
import {
  countActiveConcepts,
  emptyConcepts,
  otherDeductions,
  suggestedGrossSalary
} from "./payrollService";

describe("otherDeductions", () => {
  it("es lo que se descuenta aparte de ISR e IMSS, como Infonavit o un préstamo", () => {
    expect(
      otherDeductions({ total_deductions: 2059.6, isr_deduction: 956.87, imss_deduction: 165.73 })
    ).toBe(937);
  });

  it("da cero sin residuos de punto flotante cuando solo hay ISR e IMSS", () => {
    expect(
      otherDeductions({ total_deductions: 1708.47, isr_deduction: 1458.83, imss_deduction: 249.64 })
    ).toBe(0);
  });

  it("nunca es negativo", () => {
    expect(
      otherDeductions({ total_deductions: 100, isr_deduction: 60, imss_deduction: 40.01 })
    ).toBe(0);
  });
});

describe("suggestedGrossSalary", () => {
  it("deja el salario intacto en mensual", () => {
    expect(suggestedGrossSalary(20000, "mensual")).toBe(20000);
  });

  it("parte el salario a la mitad en quincenal", () => {
    expect(suggestedGrossSalary(20000, "quincenal")).toBe(10000);
  });

  it("reparte el salario anual entre 52 semanas", () => {
    expect(suggestedGrossSalary(20000, "semanal")).toBe(4615.38);
  });

  it("redondea a centavos y no arrastra decimales", () => {
    expect(suggestedGrossSalary(18333.33, "quincenal")).toBe(9166.67);
    expect(suggestedGrossSalary(18333.33, "semanal")).toBe(4230.77);
  });

  it("no propone un salario negativo desde cero", () => {
    expect(suggestedGrossSalary(0, "quincenal")).toBe(0);
  });
});

describe("countActiveConcepts", () => {
  it("no cuenta nada cuando el formulario esta limpio", () => {
    expect(countActiveConcepts(emptyConcepts)).toBe(0);
  });

  it("cuenta solo los conceptos con valor", () => {
    expect(
      countActiveConcepts({
        ...emptyConcepts,
        overtimeDoubleHours: 6,
        loanDeduction: 500
      })
    ).toBe(2);
  });

  it("ignora los ceros explicitos", () => {
    expect(
      countActiveConcepts({ ...emptyConcepts, bonus: 0, vacationDays: 0 })
    ).toBe(0);
  });

  it("cuenta los siete cuando todos estan puestos", () => {
    expect(
      countActiveConcepts({
        overtimeDoubleHours: 9,
        overtimeTripleHours: 3,
        christmasBonusDays: 15,
        vacationDays: 12,
        bonus: 1500,
        loanDeduction: 800,
        housingCreditDeduction: 1200
      })
    ).toBe(7);
  });
});
