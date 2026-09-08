import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ReceiptDownloadButton from "./ReceiptDownloadButton";
import { downloadReceipt } from "../services/payrollService";

vi.mock("../services/payrollService", () => ({
  downloadReceipt: vi.fn()
}));

beforeEach(() => {
  vi.clearAllMocks();
});

it("pide el comprobante de ese recibo", async () => {
  vi.mocked(downloadReceipt).mockResolvedValue(undefined);
  const user = userEvent.setup();
  render(<ReceiptDownloadButton receiptId={42} />);

  await user.click(screen.getByText("Descargar comprobante"));

  await waitFor(() => expect(downloadReceipt).toHaveBeenCalledWith(42));
});

it("acepta una etiqueta propia", () => {
  render(<ReceiptDownloadButton receiptId={42} label="Descargar recibo" />);

  expect(screen.getByText("Descargar recibo")).toBeInTheDocument();
});

it("avisa cuando la descarga falla", async () => {
  vi.mocked(downloadReceipt).mockRejectedValue(new Error("sin red"));
  const user = userEvent.setup();
  render(<ReceiptDownloadButton receiptId={42} />);

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
  render(<ReceiptDownloadButton receiptId={42} />);

  await user.click(screen.getByText("Descargar comprobante"));

  expect(screen.getByText("Preparando…")).toBeDisabled();
});

describe("despues de un intento fallido", () => {
  it("limpia el aviso al reintentar", async () => {
    vi.mocked(downloadReceipt).mockRejectedValueOnce(new Error("sin red"));
    const user = userEvent.setup();
    render(<ReceiptDownloadButton receiptId={42} />);

    await user.click(screen.getByText("Descargar comprobante"));
    expect(await screen.findByRole("alert")).toBeInTheDocument();

    vi.mocked(downloadReceipt).mockResolvedValue(undefined);
    await user.click(screen.getByText("Descargar comprobante"));

    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
  });
});
