import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import SuperadminOwnersPage from "./SuperadminOwnersPage";
import {
  createOwner,
  listOwners,
  resetOwnerPassword,
  setOwnerActive
} from "../services/superadminService";

vi.mock("../services/superadminService", () => ({
  listOwners: vi.fn(),
  createOwner: vi.fn(),
  updateOwner: vi.fn(),
  setOwnerActive: vi.fn(),
  resetOwnerPassword: vi.fn()
}));

const laura = {
  id: 5,
  name: "Laura Mendez",
  email: "laura@grupo.mx",
  is_active: true,
  companies: [{ id: 1, legal_name: "Grupo Norte", is_active: true }]
};

function renderPage() {
  return render(
    <MemoryRouter>
      <SuperadminOwnersPage />
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(listOwners).mockResolvedValue([laura]);
});

describe("listado", () => {
  it("muestra a cada dueño con sus empresas", async () => {
    renderPage();

    expect(await screen.findByText("Laura Mendez")).toBeInTheDocument();
    expect(screen.getByText(/laura@grupo.mx · Grupo Norte/)).toBeInTheDocument();
  });

  it("avisa cuando no hay dueños", async () => {
    vi.mocked(listOwners).mockResolvedValue([]);
    renderPage();

    expect(await screen.findByText("Todavía no hay dueños")).toBeInTheDocument();
  });
});

describe("alta", () => {
  it("muestra la contraseña temporal una sola vez", async () => {
    const user = userEvent.setup();
    vi.mocked(createOwner).mockResolvedValue({
      owner: { id: 6, name: "Pedro Ruiz", email: "pedro@sur.mx", is_active: true, companies: [] },
      temporary_password: "Xk7mQ2pRt9Zc"
    });
    renderPage();
    await screen.findByText("Laura Mendez");

    await user.click(screen.getByRole("button", { name: /Nuevo dueño/ }));
    await user.type(screen.getByLabelText("Nombre completo"), "Pedro Ruiz");
    await user.type(screen.getByLabelText("Correo"), "pedro@sur.mx");
    await user.click(screen.getByRole("button", { name: "Dar de alta" }));

    expect(createOwner).toHaveBeenCalledWith({ name: "Pedro Ruiz", email: "pedro@sur.mx" });
    expect(await screen.findByText("Xk7mQ2pRt9Zc")).toBeInTheDocument();
    expect(screen.getByText("Pedro Ruiz")).toBeInTheDocument();
  });

  it("explica el correo repetido", async () => {
    const user = userEvent.setup();
    vi.mocked(createOwner).mockRejectedValue({ response: { status: 409 } });
    renderPage();
    await screen.findByText("Laura Mendez");

    await user.click(screen.getByRole("button", { name: /Nuevo dueño/ }));
    await user.type(screen.getByLabelText("Nombre completo"), "Laura");
    await user.type(screen.getByLabelText("Correo"), "laura@grupo.mx");
    await user.click(screen.getByRole("button", { name: "Dar de alta" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Ese correo ya está registrado");
  });
});

describe("acciones", () => {
  it("pide confirmación antes de restablecer la contraseña", async () => {
    const user = userEvent.setup();
    vi.mocked(resetOwnerPassword).mockResolvedValue({
      owner_id: 5,
      name: "Laura Mendez",
      email: "laura@grupo.mx",
      temporary_password: "Nn4pQ8rTw2Ya"
    });
    renderPage();
    await screen.findByText("Laura Mendez");

    await user.click(screen.getByRole("button", { name: "Restablecer contraseña" }));
    expect(resetOwnerPassword).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Restablecer" }));

    expect(resetOwnerPassword).toHaveBeenCalledWith(5);
    expect(await screen.findByText("Nn4pQ8rTw2Ya")).toBeInTheDocument();
  });

  it("explica por qué no puede desactivar al último dueño de una empresa", async () => {
    const user = userEvent.setup();
    vi.mocked(setOwnerActive).mockRejectedValue({
      response: {
        status: 409,
        data: { detail: "Estas empresas se quedarían sin ningún dueño activo: Grupo Norte" }
      }
    });
    renderPage();
    await screen.findByText("Laura Mendez");

    await user.click(screen.getByRole("button", { name: "Desactivar" }));
    await user.click(screen.getByRole("button", { name: "Desactivar" }));

    await waitFor(() => expect(setOwnerActive).toHaveBeenCalledWith(5, false));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Grupo Norte. Asígnales otro dueño antes de desactivarlo."
    );
  });
});
