import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ReceiptCard from "./ReceiptCard";
import { downloadReceipt } from "../services/payrollService";

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

beforeEach(() => {
  vi.clearAllMocks();
});

describe("contenido", () => {
  it("muestra el periodo del recibo y no su fecha de captura", () => {
    render(<ReceiptCard receipt={receipt} />);

    expect(screen.getByText("Septiembre de 2026")).toBeInTheDocument();
  });

  it("muestra el desglose y el neto", () => {
    render(<ReceiptCard receipt={receipt} />);

    expect(screen.getByText("$17,804.14")).toBeInTheDocument();
    expect(screen.getByText("$21,000.00")).toBeInTheDocument();
  });
});

describe("descarga", () => {
  it("pide el comprobante de ese recibo", async () => {
    vi.mocked(downloadReceipt).mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<ReceiptCard receipt={receipt} />);

    await user.click(screen.getByText("Descargar comprobante"));

    await waitFor(() => expect(downloadReceipt).toHaveBeenCalledWith(42));
  });

  it("avisa cuando la descarga falla", async () => {
    vi.mocked(downloadReceipt).mockRejectedValue(new Error("sin red"));
    const user = userEvent.setup();
    render(<ReceiptCard receipt={receipt} />);

    await user.click(screen.getByText("Descargar comprobante"));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "No se pudo descargar"
    );
  });

  it("no deja pedirla dos veces mientras se prepara", async () => {
    vi.mocked(downloadReceipt).mockImplementation(
      () => new Promise(() => undefined)
    );
    const user = userEvent.setup();
    render(<ReceiptCard receipt={receipt} />);

    await user.click(screen.getByText("Descargar comprobante"));

    expect(screen.getByText("Preparando…")).toBeDisabled();
  });
});
