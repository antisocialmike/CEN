import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import OwnerCompaniesPage from "./OwnerCompaniesPage";
import {
  assignAdmin,
  inviteAdmin,
  listOwnerCompanies,
  OwnerCompany,
  setOwnerCompanyActive,
  setRiskPremium,
  unassignAdmin
} from "../services/ownerService";

vi.mock("../services/ownerService", () => ({
  listOwnerCompanies: vi.fn(),
  updateOwnerCompany: vi.fn(),
  setOwnerCompanyActive: vi.fn(),
  setRiskPremium: vi.fn(),
  inviteAdmin: vi.fn(),
  assignAdmin: vi.fn(),
  unassignAdmin: vi.fn()
}));

const norte: OwnerCompany = {
  id: 1,
  legal_name: "Grupo Norte SA de CV",
  trade_name: "Norte",
  rfc: "GNO010101AB1",
  registro_patronal: null,
  entidad_federativa: "NLE",
  is_active: true,
  created_at: "2026-01-01T00:00:00Z",
  active_employees: 3,
  risk_premium: { rate: "0.0054355", valid_from: "2026-03-01" },
  admins: [
    {
      id: 3, name: "Fernanda Ríos", email: "fer@norte.mx",
      is_active: true, assigned_at: "2026-01-01T00:00:00Z"
    }
  ]
};

function renderPage() {
  return render(
    <MemoryRouter>
      <OwnerCompaniesPage />
    </MemoryRouter>
  );
}

async function card(): Promise<HTMLElement> {
  const heading = await screen.findByRole("heading", { name: /Grupo Norte SA de CV/ });
  return heading.closest("section") as HTMLElement;
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(listOwnerCompanies).mockResolvedValue([norte]);
});

describe("mis empresas", () => {
  it("muestra cada empresa con sus datos y sus administradores", async () => {
    renderPage();
    const section = await card();

    expect(within(section).getByText(/RFC GNO010101AB1 · Nuevo León · 3 empleados activos/)).toBeInTheDocument();
    expect(within(section).getByText("Fernanda Ríos")).toBeInTheDocument();
  });

  it("pide confirmación antes de desactivar la empresa", async () => {
    const user = userEvent.setup();
    vi.mocked(setOwnerCompanyActive).mockResolvedValue({ ...norte, is_active: false });
    renderPage();
    const section = await card();

    await user.click(within(section).getByRole("button", { name: "Desactivar" }));
    expect(setOwnerCompanyActive).not.toHaveBeenCalled();
    expect(within(section).getByText(/sus empleados no podrán entrar/)).toBeInTheDocument();
    await user.click(within(section).getByRole("button", { name: "Desactivar" }));

    expect(setOwnerCompanyActive).toHaveBeenCalledWith(1, false);
    expect(await screen.findByText("Inactiva")).toBeInTheDocument();
  });
});

describe("prima de riesgo", () => {
  it("muestra la vigente en por ciento, como se declara", async () => {
    renderPage();
    const section = await card();

    expect(within(section).getByText("0.54355 % desde el 1 de marzo de 2026.")).toBeInTheDocument();
  });

  it("registra una prima nueva con su fecha", async () => {
    const user = userEvent.setup();
    vi.mocked(setRiskPremium).mockResolvedValue({
      ...norte,
      risk_premium: { rate: "0.0112", valid_from: "2027-03-01" }
    });
    renderPage();
    const section = await card();

    await user.click(within(section).getByRole("button", { name: "Registrar prima nueva" }));
    const rate = within(section).getByLabelText("Prima (%)");
    await user.clear(rate);
    await user.type(rate, "1.12");
    await user.type(within(section).getByLabelText("Vigente desde"), "2027-03-01");
    await user.click(within(section).getByRole("button", { name: "Registrar prima" }));

    expect(setRiskPremium).toHaveBeenCalledWith(1, { ratePercent: "1.12", validFrom: "2027-03-01" });
    expect(await within(section).findByText("1.12 % desde el 1 de marzo de 2027.")).toBeInTheDocument();
  });

  it("avisa cuando la empresa no tiene prima", async () => {
    vi.mocked(listOwnerCompanies).mockResolvedValue([{ ...norte, risk_premium: null }]);
    renderPage();
    const section = await card();

    expect(within(section).getByText(/el costo patronal no incluye riesgos de trabajo/)).toBeInTheDocument();
  });
});

describe("administradores", () => {
  it("invita a uno nuevo y muestra su contraseña temporal", async () => {
    const user = userEvent.setup();
    vi.mocked(inviteAdmin).mockResolvedValue({
      company: norte,
      admin_id: 31,
      temporary_password: "Xk7mQ2pRt9Zc"
    });
    renderPage();
    const section = await card();

    await user.click(within(section).getByRole("button", { name: /Invitar administrador/ }));
    await user.type(within(section).getByLabelText("Nombre completo"), "Pablo Soto");
    await user.type(within(section).getByLabelText("Correo"), "pablo@norte.mx");
    await user.click(within(section).getByRole("button", { name: "Invitar" }));

    expect(inviteAdmin).toHaveBeenCalledWith(1, { name: "Pablo Soto", email: "pablo@norte.mx" });
    expect(await screen.findByText("Xk7mQ2pRt9Zc")).toBeInTheDocument();
  });

  it("explica cuando no hay un administrador con ese correo", async () => {
    const user = userEvent.setup();
    vi.mocked(assignAdmin).mockRejectedValue({ response: { status: 404 } });
    renderPage();
    const section = await card();

    await user.click(within(section).getByRole("button", { name: "Asignar uno existente" }));
    await user.type(within(section).getByLabelText("Correo del administrador"), "ana@norte.mx");
    await user.click(within(section).getByRole("button", { name: "Asignar" }));

    expect(assignAdmin).toHaveBeenCalledWith(1, "ana@norte.mx");
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "No hay un administrador activo con ese correo"
    );
  });

  it("retira a un administrador sin desactivar su cuenta", async () => {
    const user = userEvent.setup();
    vi.mocked(unassignAdmin).mockResolvedValue({ ...norte, admins: [] });
    renderPage();
    const section = await card();

    await user.click(within(section).getByRole("button", { name: "Retirar" }));

    expect(unassignAdmin).toHaveBeenCalledWith(1, 3);
    expect(await screen.findByText(/Su cuenta sigue activa/)).toBeInTheDocument();
    expect(within(section).getByText("Nadie administra esta empresa todavía.")).toBeInTheDocument();
  });
});
