import { expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import ReceiptCard from "./ReceiptCard";

vi.mock("../services/payrollService", () => ({
  downloadReceipt: vi.fn()
}));

const receipt = {
  id: 42,
  employee_id: 3,
  employee_name: "Ana Lopez",
  period: "2026-09-01",
  gross_salary: 21000,
  isr_deduction: 2612.86,
  imss_deduction: 583,
  net_salary: 17804.14,
  processed_by: "admin@cen.com",
  created_at: "2026-09-08T10:30:00"
};

it("muestra el periodo del recibo y no su fecha de captura", () => {
  render(<ReceiptCard receipt={receipt} />);

  expect(screen.getByText("Septiembre de 2026")).toBeInTheDocument();
});

it("muestra el desglose y el neto", () => {
  render(<ReceiptCard receipt={receipt} />);

  expect(screen.getByText("$17,804.14")).toBeInTheDocument();
  expect(screen.getByText("$21,000.00")).toBeInTheDocument();
});

it("ofrece descargar el comprobante", () => {
  render(<ReceiptCard receipt={receipt} />);

  expect(screen.getByText("Descargar comprobante")).toBeInTheDocument();
});
