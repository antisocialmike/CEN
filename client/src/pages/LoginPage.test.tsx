import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import LoginPage from "./LoginPage";
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
