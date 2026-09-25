import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import LoginPage from "./LoginPage";
import ProtectedRoute from "../components/ProtectedRoute";
import { login } from "../services/authService";
import { saveSession } from "../services/authSession";
import { desglosar } from "../components/landing/calculoNomina";

vi.mock("../services/authService", () => ({ login: vi.fn() }));

function montar() {
  return render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>
  );
}

describe("el escaparate del login", () => {
  it("dice que los datos son de muestra", () => {
    montar();
    expect(screen.getByText(/Ejemplo con datos de muestra/i)).toBeInTheDocument();
  });

  it("la cifra sale del calculo del producto, no escrita a mano", () => {
    montar();

    const esperado = desglosar(22000, "mensual");
    const formateado = new Intl.NumberFormat("es-MX", {
      style: "currency",
      currency: "MXN"
    }).format(esperado.neto);

    expect(screen.getByText(formateado)).toBeInTheDocument();
  });

  it("el escaparate no le roba el nombre accesible al formulario", () => {
    const { container } = montar();
    const hijos = [...(container.querySelector(".auth-page")?.children ?? [])];

    expect(hijos[0]?.tagName).toBe("MAIN");
    expect(hijos[1]?.tagName).toBe("ASIDE");
  });

  it("sigue habiendo un formulario utilizable", () => {
    montar();
    expect(screen.getByLabelText("Correo")).toBeInTheDocument();
    expect(screen.getByLabelText("Contraseña")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Ingresar/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Olvidaste tu contraseña/i })).toBeInTheDocument();
  });
});

describe("los errores del login", () => {
  async function entrarCon(error: unknown) {
    vi.mocked(login).mockRejectedValueOnce(error);
    montar();
    const usuario = userEvent.setup();
    await usuario.type(screen.getByLabelText("Correo"), "ana@cen.com");
    await usuario.type(screen.getByLabelText("Contraseña"), "secreta123");
    await usuario.click(screen.getByRole("button", { name: /Ingresar/i }));
  }

  it("un 401 habla de credenciales", async () => {
    await entrarCon({ response: { status: 401 } });
    expect(await screen.findByText(/Correo o contraseña incorrectos/i)).toBeInTheDocument();
  });

  it("un 503 no culpa a la contraseña", async () => {
    await entrarCon({ response: { status: 503, data: { detail: "Base de datos no disponible" } } });
    expect(await screen.findByText(/no puede acceder a sus datos/i)).toBeInTheDocument();
    expect(screen.queryByText(/Correo o contraseña incorrectos/i)).not.toBeInTheDocument();
  });

  it("un bloqueo por intentos muestra lo que dice el servidor", async () => {
    await entrarCon({
      response: { status: 429, data: { detail: "Demasiados intentos fallidos. Vuelve a intentarlo en 5 minutos" } }
    });
    expect(await screen.findByText(/Vuelve a intentarlo en 5 minutos/i)).toBeInTheDocument();
  });

  it("una cuenta desactivada lo dice", async () => {
    await entrarCon({ response: { status: 403, data: { detail: "Esta cuenta esta desactivada" } } });
    expect(await screen.findByText(/Esta cuenta esta desactivada/i)).toBeInTheDocument();
  });

  it("sin respuesta del servidor avisa de la conexion", async () => {
    await entrarCon(new Error("Network Error"));
    expect(await screen.findByText(/No se pudo conectar con el servidor/i)).toBeInTheDocument();
  });
});

describe("con la sesion ya abierta", () => {
  const sesionDeAna = {
    accessToken: "token-abc",
    role: "employee" as const,
    name: "Ana Ramírez",
    employeeId: 7,
    mustChangePassword: false
  };

  // Con ProtectedRoute de verdad: el desvio al cambio de contrasena es cosa suya.
  function montarConRutas() {
    return render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/cambiar-contrasena" element={<p>cambio de contrasena</p>} />
          </Route>
          <Route element={<ProtectedRoute allowedRole="employee" />}>
            <Route path="/empleado" element={<p>panel de empleado</p>} />
          </Route>
        </Routes>
      </MemoryRouter>
    );
  }

  afterEach(() => {
    localStorage.clear();
  });

  it("manda al panel de su rol sin pedir la contraseña otra vez", () => {
    saveSession(sesionDeAna);
    montarConRutas();

    expect(screen.getByText("panel de empleado")).toBeInTheDocument();
    expect(screen.queryByLabelText("Correo")).not.toBeInTheDocument();
  });

  it("si tiene pendiente cambiar la contraseña, termina ahi", () => {
    saveSession({ ...sesionDeAna, mustChangePassword: true });
    montarConRutas();

    expect(screen.getByText("cambio de contrasena")).toBeInTheDocument();
  });

  it("con el token vencido muestra el formulario", () => {
    saveSession({ ...sesionDeAna, accessToken: `x.${btoa(JSON.stringify({ exp: 1 }))}.y` });
    montarConRutas();

    expect(screen.getByLabelText("Correo")).toBeInTheDocument();
  });
});
