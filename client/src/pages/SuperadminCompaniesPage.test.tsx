import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import SuperadminCompaniesPage from "./SuperadminCompaniesPage";
import {
  assignCompanyOwner,
  createCompany,
  listCompanies,
  listOwners,
  unassignCompanyOwner
} from "../services/superadminService";

vi.mock("../services/superadminService", async (importOriginal) => {
  const original = await importOriginal<typeof import("../services/superadminService")>();
  return {
    ENTIDADES_FEDERATIVAS: original.ENTIDADES_FEDERATIVAS,
    listCompanies: vi.fn(),
    listOwners: vi.fn(),
    createCompany: vi.fn(),
    updateCompany: vi.fn(),
    assignCompanyOwner: vi.fn(),
    unassignCompanyOwner: vi.fn()
  };
});

const laura = { id: 5, name: "Laura Mendez", email: "laura@grupo.mx", is_active: true, companies: [] };
const pedro = { id: 6, name: "Pedro Ruiz", email: "pedro@sur.mx", is_active: true, companies: [] };

const norte = {
  id: 1,
  legal_name: "Grupo Norte SA de CV",
  trade_name: "Norte",
  rfc: "GNO010101AB1",
  registro_patronal: null,
  entidad_federativa: "NLE" as const,
  is_active: true,
  created_at: "2026-09-23T00:00:00Z",
  owners: [{ id: 5, name: "Laura Mendez", is_active: true }]
};

function renderPage() {
  return render(
    <MemoryRouter>
      <SuperadminCompaniesPage />
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(listCompanies).mockResolvedValue([norte]);
  vi.mocked(listOwners).mockResolvedValue([laura, pedro]);
});

describe("listado", () => {
  it("muestra cada empresa con sus datos y sus dueños", async () => {
    renderPage();

    expect(await screen.findByText("Grupo Norte SA de CV")).toBeInTheDocument();
    expect(screen.getByText("Norte · RFC GNO010101AB1 · Nuevo León")).toBeInTheDocument();
    expect(screen.getByRole("list", { name: "Dueños de Grupo Norte SA de CV" })).toHaveTextContent(
      "Laura Mendez"
    );
  });
});

describe("alta", () => {
  it("registra la empresa con su primer dueño", async () => {
    const user = userEvent.setup();
    vi.mocked(createCompany).mockResolvedValue({ ...norte, id: 2, legal_name: "Sur SA" });
    renderPage();
    await screen.findByText("Grupo Norte SA de CV");

    await user.click(screen.getByRole("button", { name: /Nueva empresa/ }));
    await user.type(screen.getByLabelText("Razón social"), "Sur SA");
    await user.type(screen.getByLabelText("RFC"), "sur010101ab1");
    await user.selectOptions(screen.getByLabelText("Dueño"), "6");
    await user.click(screen.getByRole("button", { name: "Registrar empresa" }));

    expect(createCompany).toHaveBeenCalledWith(
      expect.objectContaining({ legalName: "Sur SA", rfc: "SUR010101AB1" }),
      6
    );
    expect(await screen.findByText("Sur SA quedó registrada.")).toBeInTheDocument();
  });

  it("pide un dueño antes de registrar la primera empresa", async () => {
    const user = userEvent.setup();
    vi.mocked(listOwners).mockResolvedValue([]);
    renderPage();
    await screen.findByText("Grupo Norte SA de CV");

    await user.click(screen.getByRole("button", { name: /Nueva empresa/ }));

    expect(screen.getByText("Primero da de alta a un dueño")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Registrar empresa" })).not.toBeInTheDocument();
  });
});

describe("dueños de la empresa", () => {
  it("solo ofrece asignar a dueños activos que aún no están", async () => {
    const user = userEvent.setup();
    vi.mocked(assignCompanyOwner).mockResolvedValue({
      ...norte,
      owners: [...norte.owners, { id: 6, name: "Pedro Ruiz", is_active: true }]
    });
    renderPage();
    await screen.findByText("Grupo Norte SA de CV");

    const select = screen.getByLabelText("Sumar dueño");
    expect(select).not.toHaveTextContent("Laura Mendez");
    await user.selectOptions(select, "6");
    await user.click(screen.getByRole("button", { name: "Asignar" }));

    expect(assignCompanyOwner).toHaveBeenCalledWith(1, 6);
    expect(
      await screen.findByRole("button", { name: "Quitar a Pedro Ruiz de Grupo Norte SA de CV" })
    ).toBeInTheDocument();
  });

  it("explica por qué no puede quitar al último dueño", async () => {
    const user = userEvent.setup();
    vi.mocked(unassignCompanyOwner).mockRejectedValue({
      response: {
        status: 409,
        data: { detail: "Estas empresas se quedarían sin ningún dueño activo: Grupo Norte SA de CV" }
      }
    });
    renderPage();
    await screen.findByText("Grupo Norte SA de CV");

    await user.click(
      screen.getByRole("button", { name: "Quitar a Laura Mendez de Grupo Norte SA de CV" })
    );

    expect(unassignCompanyOwner).toHaveBeenCalledWith(1, 5);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Asigna otro dueño antes de quitar a este."
    );
  });
});
