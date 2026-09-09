import { expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import ReceiptCard from "./ReceiptCard";
import { PayrollItem } from "../services/payrollService";

vi.mock("../services/payrollService", () => ({
  downloadReceipt: vi.fn()
}));

const items: PayrollItem[] = [
  {
    kind: "perception",
    concept: "sueldo",
    description: "Sueldo del periodo",
    amount: 21000,
    taxable: 21000,
    exempt: 0
  },
  {
    kind: "perception",
    concept: "aguinaldo",
    description: "Aguinaldo (15 dias)",
    amount: 10500,
    taxable: 6980.7,
    exempt: 3519.3
  },
  {
    kind: "deduction",
    concept: "isr",
    description: "ISR retenido",
    amount: 2612.86,
    taxable: 0,
    exempt: 0
  },
  {
    kind: "deduction",
    concept: "infonavit",
    description: "Credito Infonavit",
    amount: 1200,
    taxable: 0,
    exempt: 0
  }
];

const receipt = {
  id: 42,
  employee_id: 3,
  employee_name: "Ana Lopez",
  period_start: "2026-09-01",
  period_end: "2026-09-30",
  periodicity: "mensual" as const,
  paid_days: 30,
  gross_salary: 21000,
  isr_deduction: 2612.86,
  imss_deduction: 583,
  net_salary: 27687.14,
  total_perceptions: 31500,
  total_deductions: 3812.86,
  taxable_base: 27980.7,
  items,
  processed_by: "admin@cen.com",
  created_at: "2026-09-08T10:30:00"
};

it("muestra el periodo del recibo y no su fecha de captura", () => {
  render(<ReceiptCard receipt={receipt} />);

  expect(screen.getByText("Septiembre de 2026")).toBeInTheDocument();
});

it("desglosa cada concepto por percepciones y deducciones", () => {
  render(<ReceiptCard receipt={receipt} />);

  expect(screen.getByText("Sueldo del periodo")).toBeInTheDocument();
  expect(screen.getByText("Aguinaldo (15 dias)")).toBeInTheDocument();
  expect(screen.getByText("ISR retenido")).toBeInTheDocument();
  expect(screen.getByText("Credito Infonavit")).toBeInTheDocument();
});

it("muestra los totales de cada grupo y el neto", () => {
  render(<ReceiptCard receipt={receipt} />);

  expect(screen.getByText("$31,500.00")).toBeInTheDocument();
  expect(screen.getByText("$27,687.14")).toBeInTheDocument();
});

it("ofrece descargar el comprobante", () => {
  render(<ReceiptCard receipt={receipt} />);

  expect(screen.getByText("Descargar comprobante")).toBeInTheDocument();
});
