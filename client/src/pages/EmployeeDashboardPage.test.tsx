import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import EmployeeDashboardPage from "./EmployeeDashboardPage";
import {
  getMyReceiptsPage,
  getMySummary,
  MySummary,
  PayrollReceipt
} from "../services/payrollService";

// Las etiquetas son las de verdad; solo se simulan las llamadas a la API.
vi.mock("../services/payrollService", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../services/payrollService")>()),
  getMySummary: vi.fn(),
  getMyReceiptsPage: vi.fn()
}));

function receipt(id: number, start: string, end: string, net: number): PayrollReceipt {
  return {
    id,
    employee_id: 7,
    period_start: start,
    period_end: end,
    periodicity: "quincenal",
    paid_days: 15,
    gross_salary: 9000,
    isr_deduction: 1100,
    imss_deduction: 400,
    net_salary: net,
    total_perceptions: 9000,
    total_deductions: 1500,
    taxable_base: 9000,
    items: [],
    processed_by: "Fernanda Ríos",
    created_at: end + "T18:00:00Z"
  };
}

function summary(overrides: Partial<MySummary> = {}): MySummary {
  const point = (id: number, start: string, end: string, net: number) => ({
    id,
    period_start: start,
    period_end: end,
    periodicity: "quincenal" as const,
    net_salary: net,
    total_perceptions: 9000
  });
  return {
    latest: point(12, "2026-09-01", "2026-09-15", 7500),
    next_period: { periodicity: "quincenal", start: "2026-09-16", end: "2026-09-30" },
    year_to_date: {
      year: 2026,
      gross_payroll: 18000,
      isr_withheld: 2200,
      imss_withheld: 800,
      net_paid: 15000,
      receipts: 2
    },
    recent: [
      point(11, "2026-08-16", "2026-08-31", 7500),
      point(12, "2026-09-01", "2026-09-15", 7500)
    ],
    ...overrides
  };
}

function pagina(items: PayrollReceipt[], total = items.length, page = 1) {
  return { items, total, page, page_size: 20 };
}

function renderPage(ruta = "/empleado") {
  return render(
    <MemoryRouter initialEntries={[ruta]}>
      <EmployeeDashboardPage />
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getMySummary).mockResolvedValue(summary());
  vi.mocked(getMyReceiptsPage).mockResolvedValue(
    pagina([
      receipt(12, "2026-09-01", "2026-09-15", 7500),
      receipt(11, "2026-08-16", "2026-08-31", 7500)
    ])
  );
});

describe("tablero del empleado", () => {
  it("muestra su último neto, el siguiente periodo estimado y lo del año", async () => {
    renderPage();

    const ultimo = (await screen.findByText("Último neto recibido")).closest(".stat-card");
    expect(within(ultimo as HTMLElement).getByText("$7,500.00")).toBeInTheDocument();

    const siguiente = screen.getByText("Siguiente periodo (estimado)").closest(".stat-card");
    expect(within(siguiente as HTMLElement).getByText(/16 al 30 de septiembre/)).toBeInTheDocument();
    expect(within(siguiente as HTMLElement).getByText(/Quincenal, como tu último recibo/)).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: "Lo que llevas en 2026" })).toBeInTheDocument();
    const isr = screen.getByText("ISR retenido").closest(".stat-card");
    expect(within(isr as HTMLElement).getByText("$2,200.00")).toBeInTheDocument();
    const imss = screen.getByText("IMSS retenido").closest(".stat-card");
    expect(within(imss as HTMLElement).getByText("$800.00")).toBeInTheDocument();
  });

  it("grafica el neto de sus últimos periodos con su tabla", async () => {
    renderPage();

    expect(await screen.findByRole("heading", { name: "Tu neto por periodo" })).toBeInTheDocument();
    expect(screen.getByText("Tus últimos 2 recibos.")).toBeInTheDocument();
    const tabla = screen.getByRole("table", { name: "Neto recibido por periodo" });
    expect(within(tabla).getAllByRole("row")).toHaveLength(3);
    expect(within(tabla).getByText("16 al 31 de agosto de 2026")).toBeInTheDocument();
  });

  it("lista sus recibos y pide la primera página", async () => {
    renderPage();

    expect(await screen.findByText(/Recibo #12/)).toBeInTheDocument();
    expect(screen.getByText(/Recibo #11/)).toBeInTheDocument();
    expect(getMyReceiptsPage).toHaveBeenCalledWith(1);
    // Con una sola página no hay controles.
    expect(screen.queryByRole("navigation", { name: "Páginas de recibos" })).not.toBeInTheDocument();
  });

  it("pagina sus recibos desde la URL", async () => {
    vi.mocked(getMyReceiptsPage).mockResolvedValue(
      pagina([receipt(3, "2025-12-16", "2025-12-31", 7000)], 25, 2)
    );
    const user = userEvent.setup();
    renderPage("/empleado?pagina=2");

    expect(await screen.findByText(/Recibo #3/)).toBeInTheDocument();
    expect(getMyReceiptsPage).toHaveBeenCalledWith(2);

    const paginas = screen.getByRole("navigation", { name: "Páginas de recibos" });
    await user.click(within(paginas).getByRole("button", { name: /Anterior/ }));
    expect(getMyReceiptsPage).toHaveBeenLastCalledWith(1);
  });

  it("sin recibos muestra un solo aviso", async () => {
    vi.mocked(getMySummary).mockResolvedValue(
      summary({
        latest: null,
        next_period: null,
        recent: [],
        year_to_date: {
          year: 2026,
          gross_payroll: 0,
          isr_withheld: 0,
          imss_withheld: 0,
          net_paid: 0,
          receipts: 0
        }
      })
    );
    vi.mocked(getMyReceiptsPage).mockResolvedValue(pagina([]));
    renderPage();

    expect(await screen.findByText("Todavía no tienes recibos")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Historial" })).not.toBeInTheDocument();
    expect(screen.queryByText("Último neto recibido")).not.toBeInTheDocument();
  });

  it("si falla el resumen, sus recibos se siguen viendo", async () => {
    vi.mocked(getMySummary).mockRejectedValue(new Error("red"));
    renderPage();

    expect(await screen.findByText(/No pudimos cargar tu resumen/)).toBeInTheDocument();
    expect(await screen.findByText(/Recibo #12/)).toBeInTheDocument();
  });

  it("si fallan los recibos, lo dice sin esconder el resumen", async () => {
    vi.mocked(getMyReceiptsPage).mockRejectedValue(new Error("red"));
    renderPage();

    expect(await screen.findByText(/No pudimos cargar tus recibos/)).toBeInTheDocument();
    expect(await screen.findByText("Último neto recibido")).toBeInTheDocument();
  });

  it("mientras carga lo anuncia a los lectores de pantalla", () => {
    vi.mocked(getMySummary).mockReturnValue(new Promise(() => {}));
    vi.mocked(getMyReceiptsPage).mockReturnValue(new Promise(() => {}));
    renderPage();

    expect(screen.getByText("Cargando tu resumen")).toBeInTheDocument();
    expect(screen.getByText("Cargando tus recibos")).toBeInTheDocument();
  });
});
