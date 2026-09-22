import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { claveDeTransicion } from "./routes/claveDeTransicion";
import EsqueletoPanel from "./components/EsqueletoPanel";

function sesion(rol: "admin" | "employee") {
  localStorage.setItem("cen_access_token", "token-de-prueba");
  localStorage.setItem("cen_user_role", rol);
  localStorage.setItem("cen_user_name", "Prueba");
  localStorage.setItem("cen_must_change_password", "false");
}

afterEach(() => {
  localStorage.clear();
});

it("login se monta sin pasar por el loader: la transicion desde la landing no parpadea", () => {
  render(
    <MemoryRouter initialEntries={["/login"]}>
      <App />
    </MemoryRouter>
  );

  expect(
    screen.getByRole("heading", { name: "Inicia sesión" })
  ).toBeInTheDocument();
  expect(screen.queryByText(/Cargando CEN Payroll/i)).not.toBeInTheDocument();
});

it("el arranque en frio de la landing si enseña el splash", () => {
  render(
    <MemoryRouter initialEntries={["/"]}>
      <App />
    </MemoryRouter>
  );

  expect(screen.getByText(/Cargando CEN Payroll/i)).toBeInTheDocument();
});

it.each([
  ["/password-recovery", "Restablecer contraseña"],
  ["/password-reset-verify", "Verificar código"]
])("%s se monta sin pasar por el splash", (ruta, titulo) => {
  render(
    <MemoryRouter initialEntries={[ruta]}>
      <App />
    </MemoryRouter>
  );

  expect(screen.getByRole("heading", { name: titulo })).toBeInTheDocument();
  expect(screen.queryByText(/Cargando CEN Payroll/i)).not.toBeInTheDocument();
});

describe("transicion de login a los paneles", () => {
  it("un panel suspendido enseña su propio armazon, no el splash de arranque", async () => {
    vi.resetModules();
    const { default: AppFresco } = await import("./App");

    sesion("admin");

    render(
      <MemoryRouter initialEntries={["/admin"]}>
        <AppFresco />
      </MemoryRouter>
    );

    expect(document.querySelector(".dashboard-shell")).not.toBeNull();
    expect(screen.getByText("Cargando tu panel")).toBeInTheDocument();
    expect(screen.queryByText(/Cargando CEN Payroll/i)).not.toBeInTheDocument();
  });

  it("el armazon nombra el contexto segun el rol, no uno generico", () => {
    sesion("employee");

    render(
      <MemoryRouter initialEntries={["/empleado"]}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByText("Portal del empleado")).toBeInTheDocument();
  });

  it("dar de alta no recibe el esqueleto de panel ni pasa por el splash", () => {
    sesion("admin");

    render(
      <MemoryRouter initialEntries={["/admin/nuevo-empleado"]}>
        <App />
      </MemoryRouter>
    );

    expect(document.querySelector(".signup-page")).not.toBeNull();
    expect(document.querySelector(".dashboard-shell")).toBeNull();
    expect(screen.queryByText(/Cargando CEN Payroll/i)).not.toBeInTheDocument();
    expect(screen.queryByText("Cargando tu panel")).not.toBeInTheDocument();
  });
});

describe("transicion entre los paneles y cambiar contraseña", () => {
  it("cambiar contraseña se monta sin pasar por el splash", () => {
    sesion("admin");

    render(
      <MemoryRouter initialEntries={["/cambiar-contrasena"]}>
        <App />
      </MemoryRouter>
    );

    expect(
      screen.getByRole("heading", { name: /contraseña/i })
    ).toBeInTheDocument();
    expect(screen.queryByText(/Cargando CEN Payroll/i)).not.toBeInTheDocument();
  });

  it("no le pone el esqueleto de panel, que seria prometer otra pantalla", () => {
    sesion("admin");

    render(
      <MemoryRouter initialEntries={["/cambiar-contrasena"]}>
        <App />
      </MemoryRouter>
    );

    expect(document.querySelector(".dashboard-shell")).toBeNull();
    expect(document.querySelector(".auth-page")).not.toBeNull();
  });

  it("la redireccion forzada por contraseña temporal tampoco pasa por el splash", async () => {
    sesion("admin");
    localStorage.setItem("cen_must_change_password", "true");

    render(
      <MemoryRouter initialEntries={["/admin"]}>
        <App />
      </MemoryRouter>
    );

    expect(screen.queryByText(/Cargando CEN Payroll/i)).not.toBeInTheDocument();

    expect(
      await screen.findByRole("heading", { name: /contraseña/i })
    ).toBeInTheDocument();
    expect(screen.queryByText(/Cargando CEN Payroll/i)).not.toBeInTheDocument();
  });
});

describe("clave de transicion entre rutas del mismo armazon", () => {
  it("las dos rutas del panel de administracion comparten clave", () => {
    expect(claveDeTransicion("/admin")).toBe(claveDeTransicion("/admin/empleados"));
  });

  it("dar de alta no la comparte: es otra forma de pagina", () => {
    expect(claveDeTransicion("/admin/nuevo-empleado")).not.toBe(
      claveDeTransicion("/admin")
    );
  });

  it("el panel del empleado esta solo en su armazon, asi que lleva su propia clave", () => {
    const suya = claveDeTransicion("/empleado");
    expect(suya).toBe("/empleado");
    expect(suya).not.toBe(claveDeTransicion("/admin"));
  });

  it("las rutas fuera de los paneles conservan el pathname como clave", () => {
    for (const ruta of ["/", "/login", "/cambiar-contrasena", "/password-recovery"]) {
      expect(claveDeTransicion(ruta)).toBe(ruta);
    }
  });
});

describe("el armazon de panel es unico y compartido", () => {
  it("una ruta de panel pinta exactamente un armazon y una topbar", () => {
    sesion("admin");

    render(
      <MemoryRouter initialEntries={["/admin"]}>
        <App />
      </MemoryRouter>
    );

    expect(document.querySelectorAll(".dashboard-shell")).toHaveLength(1);
    expect(document.querySelectorAll(".dashboard-topbar")).toHaveLength(1);
    expect(document.querySelectorAll("#contenido")).toHaveLength(1);
  });

  it("el esqueleto no trae armazon propio: se pinta dentro del que ya hay", () => {
    render(<EsqueletoPanel />);

    expect(document.querySelector(".dashboard-shell")).toBeNull();
    expect(document.querySelector(".dashboard-topbar")).toBeNull();
    expect(screen.getByText("Cargando tu panel")).toBeInTheDocument();
    expect(
      document.querySelector('.dashboard-panel[aria-hidden="true"]')
    ).not.toBeNull();
  });

  it("la topbar nombra el contexto segun el rol", () => {
    sesion("employee");

    render(
      <MemoryRouter initialEntries={["/empleado"]}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByText("Portal del empleado")).toBeInTheDocument();
    expect(screen.queryByText("Panel de administración")).not.toBeInTheDocument();
  });
});

