import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import PasswordRecoveryPage from "./PasswordRecoveryPage";
import httpClient from "../services/httpClient";

vi.mock("../services/httpClient", () => ({ default: { post: vi.fn() } }));

function Verificacion() {
  const location = useLocation();
  return <p>Verificando {(location.state as { email: string }).email}</p>;
}

function montar() {
  return render(
    <MemoryRouter initialEntries={["/password-recovery"]}>
      <Routes>
        <Route path="/password-recovery" element={<PasswordRecoveryPage />} />
        <Route path="/password-reset-verify" element={<Verificacion />} />
      </Routes>
    </MemoryRouter>
  );
}

async function pedirCodigo(correo: string) {
  const usuario = userEvent.setup();
  await usuario.type(screen.getByLabelText("Correo"), correo);
  await usuario.click(screen.getByRole("button", { name: /Enviar código/i }));
}

beforeEach(() => {
  vi.mocked(httpClient.post).mockReset();
});

describe("la solicitud del código", () => {
  it("lleva a la verificación con el correo que lo pidió", async () => {
    vi.mocked(httpClient.post).mockResolvedValueOnce({ status: 204 });
    montar();

    await pedirCodigo("ana@cen.com");

    expect(httpClient.post).toHaveBeenCalledWith("/auth/password-reset/request", {
      email: "ana@cen.com"
    });
    expect(await screen.findByText("Verificando ana@cen.com")).toBeInTheDocument();
  });

  it("muestra el aviso del servidor cuando se pidieron demasiados", async () => {
    vi.mocked(httpClient.post).mockRejectedValueOnce({
      response: {
        status: 429,
        data: { detail: "Demasiadas solicitudes desde tu conexion. Vuelve a intentarlo en 10 minutos" }
      }
    });
    montar();

    await pedirCodigo("ana@cen.com");

    expect(await screen.findByText(/Vuelve a intentarlo en 10 minutos/)).toBeInTheDocument();
    expect(screen.queryByText(/Verificando/)).not.toBeInTheDocument();
  });
});
