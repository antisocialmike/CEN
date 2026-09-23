import { beforeEach, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TunelProvider } from "./TransicionTunel";
import { useTunel } from "../motion/tunel";

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

function Boton({ alNavegar }: { alNavegar: () => void }) {
  const pasarPorTunel = useTunel();
  return <button onClick={() => pasarPorTunel(alNavegar)}>ir</button>;
}

it("sin proveedor navega directo: una pagina suelta no depende del tunel", async () => {
  const alNavegar = vi.fn();
  render(<Boton alNavegar={alNavegar} />);

  await userEvent.click(screen.getByRole("button", { name: "ir" }));

  expect(alNavegar).toHaveBeenCalledTimes(1);
});

it("con movimiento reducido navega directo y no tapa la pantalla", async () => {
  reduceMotion.mockReturnValue(true);
  const alNavegar = vi.fn();
  render(
    <TunelProvider>
      <Boton alNavegar={alNavegar} />
    </TunelProvider>
  );

  await userEvent.click(screen.getByRole("button", { name: "ir" }));

  expect(alNavegar).toHaveBeenCalledTimes(1);
  expect(document.querySelector(".app-tunel")).toBeNull();
});

it("tapa con el logo, navega por debajo una sola vez aunque se pida dos veces y luego destapa", async () => {
  const alNavegar = vi.fn();
  render(
    <TunelProvider>
      <Boton alNavegar={alNavegar} />
    </TunelProvider>
  );

  const boton = screen.getByRole("button", { name: "ir" });
  await userEvent.click(boton);
  await userEvent.click(boton);

  expect(document.querySelector(".app-tunel")).not.toBeNull();
  expect(alNavegar).not.toHaveBeenCalled();

  await waitFor(() => expect(alNavegar).toHaveBeenCalledTimes(1), { timeout: 2000 });
  await waitFor(() => expect(document.querySelector(".app-tunel")).toBeNull(), {
    timeout: 3000
  });
  expect(alNavegar).toHaveBeenCalledTimes(1);
});

it("con origen tambien tapa, navega y destapa", async () => {
  const alNavegar = vi.fn();
  function ConOrigen() {
    const pasarPorTunel = useTunel();
    return (
      <button onClick={(e) => pasarPorTunel(alNavegar, { origen: e.currentTarget })}>
        desde aqui
      </button>
    );
  }
  render(
    <TunelProvider>
      <ConOrigen />
    </TunelProvider>
  );

  await userEvent.click(screen.getByRole("button", { name: "desde aqui" }));

  expect(document.querySelector(".app-tunel")).not.toBeNull();
  await waitFor(() => expect(alNavegar).toHaveBeenCalledTimes(1), { timeout: 2000 });
  await waitFor(() => expect(document.querySelector(".app-tunel")).toBeNull(), {
    timeout: 3000
  });
});
