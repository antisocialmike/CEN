import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import PasswordResetVerifyPage from "./PasswordResetVerifyPage";
import httpClient from "../services/httpClient";

vi.mock("../services/httpClient", () => ({ default: { post: vi.fn() } }));

function montar(state?: unknown) {
  return render(
    <MemoryRouter initialEntries={[{ pathname: "/password-reset-verify", state }]}>
      <Routes>
        <Route path="/password-reset-verify" element={<PasswordResetVerifyPage />} />
        <Route path="/login" element={<p>Pantalla de login</p>} />
      </Routes>
    </MemoryRouter>
  );
}

async function canjear(codigo: string) {
  const usuario = userEvent.setup();
  await usuario.type(screen.getByLabelText("Código de verificación"), codigo);
  await usuario.type(screen.getByLabelText("Contraseña nueva"), "nuevaClave1");
  await usuario.type(screen.getByLabelText("Repite la contraseña nueva"), "nuevaClave1");
  await usuario.click(screen.getByRole("button", { name: /Cambiar contraseña/i }));
  return usuario;
}

beforeEach(() => {
  vi.mocked(httpClient.post).mockReset();
});

describe("el canje del código", () => {
  it("trae el correo de la solicitud y lo manda con el código", async () => {
    vi.mocked(httpClient.post).mockResolvedValueOnce({ status: 204 });
    montar({ email: "ana@cen.com" });

    expect(screen.getByLabelText("Correo")).toHaveValue("ana@cen.com");
    await canjear("123456");

    expect(httpClient.post).toHaveBeenCalledWith("/auth/password-reset/verify", {
      email: "ana@cen.com",
      code: "123456",
      new_password: "nuevaClave1"
    });
    expect(await screen.findByText("Pantalla de login")).toBeInTheDocument();
  });

  it("si se entra directo, pide el correo", async () => {
    vi.mocked(httpClient.post).mockResolvedValueOnce({ status: 204 });
    montar();

    const correo = screen.getByLabelText("Correo");
    expect(correo).toHaveValue("");
    await userEvent.setup().type(correo, "luis@cen.com");
    await canjear("654321");

    expect(vi.mocked(httpClient.post).mock.calls[0][1]).toMatchObject({
      email: "luis@cen.com",
      code: "654321"
    });
  });

  it("un código que no sirve deja la pantalla con el aviso", async () => {
    vi.mocked(httpClient.post).mockRejectedValueOnce({
      response: { status: 400, data: { detail: "Codigo invalido o expirado" } }
    });
    montar({ email: "ana@cen.com" });

    await canjear("111111");

    expect(await screen.findByText(/Código inválido, expirado o ya utilizado/)).toBeInTheDocument();
  });

  it("muestra el aviso del servidor cuando hubo demasiados intentos", async () => {
    vi.mocked(httpClient.post).mockRejectedValueOnce({
      response: {
        status: 429,
        data: { detail: "Demasiadas solicitudes desde tu conexion. Vuelve a intentarlo en 3 minutos" }
      }
    });
    montar({ email: "ana@cen.com" });

    await canjear("111111");

    expect(await screen.findByText(/Vuelve a intentarlo en 3 minutos/)).toBeInTheDocument();
  });

  it("ofrece pedir otro código", () => {
    montar({ email: "ana@cen.com" });

    expect(screen.getByRole("link", { name: /Pide otro código/i })).toHaveAttribute(
      "href",
      "/password-recovery"
    );
  });
});
