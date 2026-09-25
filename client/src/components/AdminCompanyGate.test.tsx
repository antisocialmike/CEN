import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import AdminCompanyGate from "./AdminCompanyGate";
import RutaDePanel from "./RutaDePanel";
import { listMyCompanies } from "../services/adminCompanyService";
import { COMPANY_HEADER, getActiveCompanyId, setActiveCompanyId } from "../services/activeCompany";
import { saveSession } from "../services/authSession";
import httpClient from "../services/httpClient";

vi.mock("../services/adminCompanyService", () => ({ listMyCompanies: vi.fn() }));
vi.mock("../motion/tunel", () => ({ useTunel: () => (run: () => void) => run() }));

const norte = { id: 1, legal_name: "Grupo Norte SA de CV", trade_name: "Norte" };
const sur = { id: 2, legal_name: "Servicios del Sur SC", trade_name: null };

function renderGate() {
  return render(
    <MemoryRouter initialEntries={["/admin"]}>
      <Routes>
        <Route element={<AdminCompanyGate />}>
          <Route element={<RutaDePanel />}>
            <Route path="/admin" element={<p>panel de la empresa</p>} />
          </Route>
        </Route>
      </Routes>
    </MemoryRouter>
  );
}

async function requestHeaders(): Promise<Record<string, unknown>> {
  const handler = (
    httpClient.interceptors.request as unknown as {
      handlers: { fulfilled: (config: { headers: Record<string, unknown> }) => unknown }[];
    }
  ).handlers[0];
  const config = (await handler.fulfilled({ headers: {} })) as { headers: Record<string, unknown> };
  return config.headers;
}

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  sessionStorage.clear();
  saveSession({
    accessToken: "token",
    role: "admin",
    name: "Fernanda Rios",
    employeeId: 3,
    mustChangePassword: false
  });
});

describe("una sola empresa", () => {
  it("entra directo y la recuerda para las peticiones", async () => {
    vi.mocked(listMyCompanies).mockResolvedValue([norte]);
    renderGate();

    expect(await screen.findByText("panel de la empresa")).toBeInTheDocument();
    expect(getActiveCompanyId()).toBe(1);
    expect((await requestHeaders())[COMPANY_HEADER]).toBe("1");
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    expect(screen.getByText("Norte")).toBeInTheDocument();
  });
});

describe("varias empresas", () => {
  it("pide elegir antes de mostrar el panel", async () => {
    const user = userEvent.setup();
    vi.mocked(listMyCompanies).mockResolvedValue([norte, sur]);
    renderGate();

    expect(await screen.findByText("¿Con qué empresa vas a trabajar?")).toBeInTheDocument();
    expect(screen.queryByText("panel de la empresa")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Servicios del Sur/ }));

    expect(await screen.findByText("panel de la empresa")).toBeInTheDocument();
    expect(getActiveCompanyId()).toBe(2);
  });

  it("recuerda la empresa elegida en la pestaña", async () => {
    setActiveCompanyId(2);
    vi.mocked(listMyCompanies).mockResolvedValue([norte, sur]);
    renderGate();

    expect(await screen.findByText("panel de la empresa")).toBeInTheDocument();
    expect(screen.getByRole("combobox")).toHaveValue("2");
  });

  it("cambiar de empresa en la barra cambia la cabecera de las peticiones", async () => {
    const user = userEvent.setup();
    setActiveCompanyId(1);
    vi.mocked(listMyCompanies).mockResolvedValue([norte, sur]);
    renderGate();

    await user.selectOptions(await screen.findByRole("combobox"), "2");

    expect(getActiveCompanyId()).toBe(2);
    expect((await requestHeaders())[COMPANY_HEADER]).toBe("2");
    expect(await screen.findByText("panel de la empresa")).toBeInTheDocument();
  });

  it("olvida una empresa guardada a la que ya no tiene acceso", async () => {
    setActiveCompanyId(9);
    vi.mocked(listMyCompanies).mockResolvedValue([norte, sur]);
    renderGate();

    expect(await screen.findByText("¿Con qué empresa vas a trabajar?")).toBeInTheDocument();
    expect(getActiveCompanyId()).toBeNull();
  });
});

describe("sin empresas", () => {
  it("explica que no hay nada que operar", async () => {
    vi.mocked(listMyCompanies).mockResolvedValue([]);
    renderGate();

    expect(await screen.findByText("No administras ninguna empresa activa")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cerrar sesión" })).toBeInTheDocument();
  });
});

describe("la cabecera de empresa", () => {
  it("solo viaja en las peticiones de un admin", async () => {
    setActiveCompanyId(1);
    saveSession({
      accessToken: "token",
      role: "owner",
      name: "Laura",
      employeeId: 20,
      mustChangePassword: false
    });

    expect((await requestHeaders())[COMPANY_HEADER]).toBeUndefined();
  });

  it("se borra al cerrar sesión", async () => {
    const { clearSession } = await import("../services/authSession");
    setActiveCompanyId(1);

    clearSession();

    expect(getActiveCompanyId()).toBeNull();
  });
});
