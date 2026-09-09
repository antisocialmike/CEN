import { beforeEach, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import PayrollResultCard from "./PayrollResultCard";
import { downloadReceipt, PayrollItem } from "../services/payrollService";

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
    concept: "horas_extra",
    description: "Horas extra (9 dobles, 3 triples)",
    amount: 2362.5,
    taxable: 1181.25,
    exempt: 1181.25
  },
  {
    kind: "deduction",
    concept: "isr",
    description: "ISR retenido",
    amount: 2851.31,
    taxable: 0,
    exempt: 0
  },
  {
    kind: "deduction",
    concept: "prestamo",
    description: "Prestamo a la empresa",
    amount: 800,
    taxable: 0,
    exempt: 0
  }
];

const result = {
  receipt_id: 42,
  created: true,
  employee_id: 3,
  employee_name: "Ana Lopez",
  period_start: "2026-09-01",
  period_end: "2026-09-30",
  processed_by: "admin@cen.com",
  data: {
    gross_salary: 21000,
    isr_deduction: 2851.31,
    imss_deduction: 539.96,
    net_salary: 19171.23,
    total_perceptions: 23362.5,
    total_deductions: 4191.27,
    taxable_base: 22181.25,
    items
  }
};

beforeEach(() => {
  vi.clearAllMocks();
});

it("encabeza con el periodo calculado", () => {
  render(<PayrollResultCard result={result} />);

  expect(screen.getByText(/Septiembre de 2026/)).toBeInTheDocument();
});

it("desglosa las horas extra y el prestamo", () => {
  render(<PayrollResultCard result={result} />);

  expect(
    screen.getByText("Horas extra (9 dobles, 3 triples)")
  ).toBeInTheDocument();
  expect(screen.getByText("Prestamo a la empresa")).toBeInTheDocument();
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
