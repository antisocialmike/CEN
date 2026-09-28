import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Paginacion from "./Paginacion";

function montar(pagina: number, total: number) {
  const alCambiar = vi.fn();
  render(
    <Paginacion pagina={pagina} total={total} etiqueta="Páginas de usuarios" alCambiar={alCambiar} />
  );
  return alCambiar;
}

describe("Paginacion", () => {
  it("con una sola pagina no enseña controles", () => {
    montar(1, 20);

    expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
  });

  it("dice que tramo se ve, de cuantos, y en que pagina se esta", () => {
    montar(2, 45);

    const nav = screen.getByRole("navigation", { name: "Páginas de usuarios" });
    expect(nav).toHaveTextContent("21–40 de 45");
    expect(screen.getByText("Página 2 de 3")).toHaveAttribute("aria-current", "page");
  });

  it("el ultimo tramo termina en el total, no en un multiplo de 20", () => {
    montar(3, 45);

    expect(screen.getByRole("navigation")).toHaveTextContent("41–45 de 45");
  });

  it("pide la pagina de al lado", async () => {
    const usuario = userEvent.setup();
    const alCambiar = montar(2, 45);

    await usuario.click(screen.getByRole("button", { name: /Siguiente/ }));
    await usuario.click(screen.getByRole("button", { name: /Anterior/ }));

    expect(alCambiar.mock.calls).toEqual([[3], [1]]);
  });

  it("no deja ir antes de la primera ni despues de la ultima", () => {
    const { rerender } = render(
      <Paginacion pagina={1} total={45} etiqueta="Páginas" alCambiar={vi.fn()} />
    );
    expect(screen.getByRole("button", { name: /Anterior/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: /Siguiente/ })).toBeEnabled();

    rerender(<Paginacion pagina={3} total={45} etiqueta="Páginas" alCambiar={vi.fn()} />);
    expect(screen.getByRole("button", { name: /Anterior/ })).toBeEnabled();
    expect(screen.getByRole("button", { name: /Siguiente/ })).toBeDisabled();
  });
});
