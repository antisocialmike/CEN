import { beforeEach, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import PageTransition from "./PageTransition";

const reduceMotion = vi.fn(() => false);

vi.mock("motion/react", async () => {
  const actual = await vi.importActual<typeof import("motion/react")>(
    "motion/react"
  );
  return { ...actual, useReducedMotion: () => reduceMotion() };
});

beforeEach(() => {
  reduceMotion.mockReturnValue(false);
});

it("muestra el contenido de la ruta", () => {
  render(
    <PageTransition>
      <p>contenido de la pagina</p>
    </PageTransition>
  );

  expect(screen.getByText("contenido de la pagina")).toBeInTheDocument();
});

it("sigue mostrando el contenido con movimiento reducido", () => {
  reduceMotion.mockReturnValue(true);

  render(
    <PageTransition>
      <p>contenido de la pagina</p>
    </PageTransition>
  );

  expect(screen.getByText("contenido de la pagina")).toBeInTheDocument();
});

it("envuelve el contenido en un solo elemento", () => {
  const { container } = render(
    <PageTransition>
      <p>contenido de la pagina</p>
    </PageTransition>
  );

  expect(container.children).toHaveLength(1);
  expect(container.firstElementChild?.tagName).toBe("DIV");
});
