import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, useLocation } from "react-router-dom";
import SuperadminSummaryPage from "./SuperadminSummaryPage";
import { getPlatformSummary, PlatformSummary } from "../services/superadminService";

vi.mock("../services/superadminService", () => ({ getPlatformSummary: vi.fn() }));

function summary(overrides: Partial<PlatformSummary> = {}): PlatformSummary {
  return {
    companies: { active: 3, inactive: 1 },
    users: {
      owner: { active: 2, inactive: 1 },
      admin: { active: 4, inactive: 0 },
      employee: { active: 40, inactive: 6 }
    },
    orphaned: {
      total: 7,
      companies: [{ id: 1, legal_name: "Empresa principal", is_active: true }]
    },
    signups: [
      { month: "2026-08-01", companies: 1, owners: 0 },
      { month: "2026-09-01", companies: 2, owners: 1 }
    ],
    activity: [
      {
        id: 30,
        action: "company.create",
        target_type: "company",
        target_name: "Grupo Norte SA de CV",
        actor_name: "Sofía Castañeda",
        created_at: "2026-09-20T17:00:00Z"
      },
      {
        id: 29,
        action: "owner.algo_nuevo",
        target_type: "owner",
        target_name: "Laura Méndez",
        actor_name: "Sofía Castañeda",
        created_at: "2026-09-19T17:00:00Z"
      }
    ],
    ...overrides
  };
}

function RutaActual() {
  return <output data-testid="ruta">{useLocation().pathname}</output>;
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/superadmin"]}>
      <SuperadminSummaryPage />
      <RutaActual />
    </MemoryRouter>
  );
}

function tarjeta(label: string): HTMLElement {
  return screen.getByText(label).closest(".stat-card") as HTMLElement;
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getPlatformSummary).mockResolvedValue(summary());
});

describe("tablero del superadmin", () => {
  it("cuenta empresas y personas por rol, activas e inactivas", async () => {
    renderPage();

    await screen.findByText("Empresas activas");
    expect(within(tarjeta("Empresas activas")).getByText("3")).toBeInTheDocument();
    expect(within(tarjeta("Empresas activas")).getByText("1 inactiva")).toBeInTheDocument();
    expect(within(tarjeta("Dueños activos")).getByText("2")).toBeInTheDocument();
    expect(within(tarjeta("Administradores activos")).getByText("0 inactivos")).toBeInTheDocument();
    expect(within(tarjeta("Empleados activos")).getByText("6 dados de baja")).toBeInTheDocument();
  });

  it("no muestra ningún monto: solo conteos", async () => {
    renderPage();

    await screen.findByText("Empresas activas");
    expect(screen.queryByText(/\$/)).not.toBeInTheDocument();
  });

  it("señala las empresas sin dueño activo y lleva a empresas", async () => {
    const user = userEvent.setup();
    renderPage();

    const tabla = await screen.findByRole("table", { name: "Empresas sin dueño activo" });
    expect(within(tabla).getByRole("row", { name: /Empresa principal/ })).toHaveTextContent("Activa");
    expect(screen.getByText("Y 6 empresas más.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Ir a empresas" }));
    expect(screen.getByTestId("ruta")).toHaveTextContent("/superadmin/empresas");
  });

  it("si todas tienen dueño, lo dice", async () => {
    vi.mocked(getPlatformSummary).mockResolvedValue(
      summary({ orphaned: { total: 0, companies: [] } })
    );
    renderPage();

    expect(
      await screen.findByText("Todas las empresas tienen al menos un dueño activo.")
    ).toBeInTheDocument();
  });

  it("grafica las altas por mes con su tabla", async () => {
    renderPage();

    expect(
      await screen.findByRole("list", { name: "Empresas y dueños nuevos por mes" })
    ).toBeInTheDocument();
    const tabla = screen.getByRole("table", { name: "Empresas y dueños nuevos por mes" });
    const septiembre = within(tabla).getByRole("row", { name: /Septiembre de 2026/ });
    expect(within(septiembre).getAllByRole("cell").map((cell) => cell.textContent)).toEqual([
      "Septiembre de 2026",
      "2",
      "1"
    ]);
  });

  it("lista la actividad reciente con quién la hizo", async () => {
    renderPage();

    const tabla = await screen.findByRole("table", { name: "Últimos movimientos de la plataforma" });
    const alta = within(tabla).getByRole("row", { name: /Grupo Norte/ });
    expect(alta).toHaveTextContent("Alta de empresa");
    expect(alta).toHaveTextContent("Sofía Castañeda");
    // Una accion que la pantalla no conoce se muestra tal cual, no se esconde.
    expect(within(tabla).getByText("owner.algo_nuevo")).toBeInTheDocument();
  });

  it("una plataforma vacía invita a dar de alta al primer dueño", async () => {
    vi.mocked(getPlatformSummary).mockResolvedValue(
      summary({
        companies: { active: 0, inactive: 0 },
        users: {
          owner: { active: 0, inactive: 0 },
          admin: { active: 0, inactive: 0 },
          employee: { active: 0, inactive: 0 }
        },
        orphaned: { total: 0, companies: [] },
        signups: [],
        activity: []
      })
    );
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Dar de alta al primer dueño" }));
    expect(screen.getByTestId("ruta")).toHaveTextContent("/superadmin/duenos");
  });

  it("los accesos llevan a dueños y a empresas", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: "Dueños" }));
    expect(screen.getByTestId("ruta")).toHaveTextContent("/superadmin/duenos");
  });

  it("si falla, lo dice y no se queda cargando", async () => {
    vi.mocked(getPlatformSummary).mockRejectedValue(new Error("red"));
    renderPage();

    expect(await screen.findByText(/No se pudo cargar el resumen/)).toBeInTheDocument();
    expect(screen.queryByText("Cargando el resumen")).not.toBeInTheDocument();
  });

  it("mientras carga lo anuncia a los lectores de pantalla", () => {
    vi.mocked(getPlatformSummary).mockReturnValue(new Promise(() => {}));
    renderPage();

    expect(screen.getByText("Cargando el resumen")).toBeInTheDocument();
  });
});
