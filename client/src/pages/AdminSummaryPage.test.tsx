import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, useLocation } from "react-router-dom";
import AdminSummaryPage from "./AdminSummaryPage";
import { AdminSummary, getAdminSummary } from "../services/adminSummaryService";

vi.mock("../services/adminSummaryService", () => ({ getAdminSummary: vi.fn() }));

function summary(overrides: Partial<AdminSummary> = {}): AdminSummary {
  return {
    month: "2026-09-01",
    on_payroll: 12,
    pending: {
      total: 10,
      people: [
        { id: 4, name: "Javier Ontiveros", tipo_regimen: "09" },
        { id: 6, name: "Rodrigo Alcántara", tipo_regimen: "02" }
      ]
    },
    last_month: {
      month: "2026-08-01",
      gross_payroll: 45000,
      net_paid: 39000,
      isr_withheld: 4700,
      imss_withheld: 1300,
      receipts: 3,
      paid_people: 3
    },
    movements: [
      { id: 6, name: "Rodrigo Alcántara", kind: "alta", happened_at: "2026-09-10T12:00:00Z" },
      { id: 5, name: "María Elena Vázquez", kind: "baja", happened_at: "2026-08-28T12:00:00Z" }
    ],
    regimes: [
      { tipo_regimen: "02", people: 11 },
      { tipo_regimen: "09", people: 1 }
    ],
    ...overrides
  };
}

function RutaActual() {
  return <output data-testid="ruta">{useLocation().pathname}</output>;
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/admin"]}>
      <AdminSummaryPage />
      <RutaActual />
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getAdminSummary).mockResolvedValue(summary());
});

describe("resumen del admin", () => {
  it("cuenta quién sigue sin recibo este mes y lista a los primeros", async () => {
    renderPage();

    const pendientes = (await screen.findByText("Sin recibo en septiembre de 2026")).closest(
      ".stat-card"
    ) as HTMLElement;
    expect(within(pendientes).getByText("10")).toBeInTheDocument();
    expect(within(pendientes).getByText("de 12 personas en la nómina")).toBeInTheDocument();

    const tabla = screen.getByRole("table", { name: "Personas sin recibo en septiembre de 2026" });
    expect(within(tabla).getByText("Javier Ontiveros")).toBeInTheDocument();
    expect(within(tabla).getByText("Asimilado")).toBeInTheDocument();
    expect(screen.getByText("Y 8 personas más.")).toBeInTheDocument();
  });

  it("muestra cómo cerró el último mes con recibos", async () => {
    renderPage();

    expect(await screen.findByRole("heading", { name: "Último mes: Agosto de 2026" })).toBeInTheDocument();
    const totales = screen.getByRole("table", { name: "Totales de Agosto de 2026" });
    expect(within(totales).getByRole("row", { name: /ISR retenido/ })).toHaveTextContent("$4,700.00");
    expect(within(totales).getByRole("row", { name: /Neto pagado/ })).toHaveTextContent("$39,000.00");
    expect(screen.getByText("3 recibos de 3 personas, por el inicio de cada periodo.")).toBeInTheDocument();
  });

  it("lista las altas y bajas recientes y el reparto por tipo de nómina", async () => {
    renderPage();

    const movimientos = await screen.findByRole("table", { name: "Últimas altas y bajas" });
    expect(within(movimientos).getByRole("row", { name: /María Elena Vázquez/ })).toHaveTextContent(
      "Baja"
    );
    const tipos = screen.getByRole("list", { name: "Personas por tipo de nómina" });
    expect(within(tipos).getByText("Sueldos y salarios")).toBeInTheDocument();
    expect(within(tipos).getByText("Asimilados a salarios (honorarios)")).toBeInTheDocument();
  });

  it("si todos tienen recibo, lo dice en vez de una lista vacía", async () => {
    vi.mocked(getAdminSummary).mockResolvedValue(
      summary({ pending: { total: 0, people: [] } })
    );
    renderPage();

    expect(
      await screen.findByText("Todos tienen al menos un recibo de septiembre de 2026.")
    ).toBeInTheDocument();
    expect(screen.queryByRole("table", { name: /Personas sin recibo/ })).not.toBeInTheDocument();
  });

  it("sin recibos todavía, el último mes lo explica", async () => {
    vi.mocked(getAdminSummary).mockResolvedValue(summary({ last_month: null }));
    renderPage();

    expect(await screen.findByText("Todavía no se ha emitido ningún recibo.")).toBeInTheDocument();
    expect(screen.getByText("Aún no hay recibos")).toBeInTheDocument();
  });

  it("una empresa sin nadie invita a dar de alta al primer usuario", async () => {
    vi.mocked(getAdminSummary).mockResolvedValue(
      summary({
        on_payroll: 0,
        pending: { total: 0, people: [] },
        last_month: null,
        movements: [],
        regimes: [
          { tipo_regimen: "02", people: 0 },
          { tipo_regimen: "09", people: 0 }
        ]
      })
    );
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Dar de alta al primer usuario" }));
    expect(screen.getByTestId("ruta")).toHaveTextContent("/admin/nuevo-usuario");
  });

  it("los accesos rápidos llevan a calcular la nómina y a los usuarios", async () => {
    const user = userEvent.setup();
    renderPage();

    const acciones = screen.getAllByRole("button", { name: "Calcular nómina" });
    await user.click(acciones[0]);
    expect(screen.getByTestId("ruta")).toHaveTextContent("/admin/nomina");
  });

  it("si falla, lo dice y no se queda cargando", async () => {
    vi.mocked(getAdminSummary).mockRejectedValue(new Error("red"));
    renderPage();

    expect(await screen.findByText(/No se pudo cargar el resumen/)).toBeInTheDocument();
    expect(screen.queryByText("Cargando el resumen")).not.toBeInTheDocument();
  });

  it("mientras carga lo anuncia a los lectores de pantalla", () => {
    vi.mocked(getAdminSummary).mockReturnValue(new Promise(() => {}));
    renderPage();

    expect(screen.getByText("Cargando el resumen")).toBeInTheDocument();
  });
});
