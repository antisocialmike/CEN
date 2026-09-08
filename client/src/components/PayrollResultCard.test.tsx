import { beforeEach, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import PayrollResultCard from "./PayrollResultCard";
import { downloadReceipt } from "../services/payrollService";

vi.mock("../services/payrollService", () => ({
  downloadReceipt: vi.fn()
}));

const result = {
  receipt_id: 42,
  created: true,
  employee_id: 3,
  employee_name: "Ana Lopez",
  period: "2026-09",
  processed_by: "admin@cen.com",
  data: {
    gross_salary: 21000,
    isr_deduction: 2612.86,
    imss_deduction: 583,
    net_salary: 17804.14
  }
};

beforeEach(() => {
  vi.clearAllMocks();
});

it("encabeza con el periodo calculado", () => {
  render(<PayrollResultCard result={result} />);

  expect(screen.getByText(/Septiembre de 2026/)).toBeInTheDocument();
});

it("dice que se guardo cuando el recibo es nuevo", () => {
  render(<PayrollResultCard result={result} />);

  expect(screen.getByText(/Guardado como recibo/)).toBeInTheDocument();
});

it("dice que se reemplazo cuando ya existia el periodo", () => {
  render(<PayrollResultCard result={{ ...result, created: false }} />);

  expect(screen.getByText(/Recibo reemplazado/)).toBeInTheDocument();
});

it("permite descargar el comprobante recien emitido", async () => {
  vi.mocked(downloadReceipt).mockResolvedValue(undefined);
  const user = userEvent.setup();
  render(<PayrollResultCard result={result} />);

  await user.click(screen.getByText("Descargar comprobante"));

  await waitFor(() => expect(downloadReceipt).toHaveBeenCalledWith(42));
});
