import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import NetoDelPeriodo, { type Partida } from "./NetoDelPeriodo";

const partidas: Partida[] = [
  { concepto: "Salario bruto", importe: 22000, tipo: "percepcion" },
  { concepto: "ISR retenido", importe: 2810.85, tipo: "deduccion" },
  { concepto: "IMSS retenido", importe: 767.9, tipo: "deduccion" }
];

const base = {
  neto: 18421.25,
  empleado: "Ana Gutiérrez",
  periodo: "1 al 31 de agosto de 2026",
  folio: "128"
};

function montar(extra: Partial<Parameters<typeof NetoDelPeriodo>[0]> = {}) {
  return render(
    <MemoryRouter>
      <NetoDelPeriodo {...base} {...extra} />
    </MemoryRouter>
  );
}

describe("NetoDelPeriodo", () => {
  it("expone el importe completo una sola vez para lectores de pantalla", () => {
    montar({ partidas });
    expect(screen.getByText("$18,421.25")).toBeInTheDocument();
  });

  it("marca las deducciones con signo, no solo con color", () => {
    montar({ partidas });

    const fila = screen.getByText("ISR retenido").closest("div");
    expect(fila).not.toBeNull();

    const importe = within(fila!).getByText("$2,810.85").closest("dd");
    expect(importe).not.toBeNull();
    expect(importe).toHaveTextContent("−");
    expect(importe).toHaveTextContent("retenido");
  });

  it("la variante compacta omite el desglose", () => {
    montar({ partidas, variante: "compacta" });
    expect(screen.queryByText("Salario bruto")).not.toBeInTheDocument();
    expect(screen.getByText("$18,421.25")).toBeInTheDocument();
  });

  it("con href es un enlace con nombre accesible completo", () => {
    montar({ partidas, href: "/login" });

    const enlace = screen.getByRole("link", {
      name: "Recibo 128 de Ana Gutiérrez, 1 al 31 de agosto de 2026. Neto $18,421.25."
    });
    expect(enlace).toHaveAttribute("href", "/login");
  });

  it("sin href no es interactivo", () => {
    montar({ partidas });
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });

  it("el estado de carga se anuncia y no filtra datos a medias", () => {
    montar({ partidas, cargando: true });

    expect(screen.getByText("Cargando el neto del periodo")).toBeInTheDocument();
    expect(screen.queryByText("$18,421.25")).not.toBeInTheDocument();
    expect(screen.queryByText("Ana Gutiérrez")).not.toBeInTheDocument();
  });

  it("redondea los centavos en vez de truncarlos", () => {
    montar({ neto: 1999.999, empleado: "Luis Márquez", periodo: "Agosto", folio: "9" });
    expect(screen.getByText("$2,000.00")).toBeInTheDocument();
  });

  it("los centavos visibles nunca desbordan a tres digitos", () => {
    const { container } = montar({
      neto: 1999.999,
      empleado: "Luis Márquez",
      periodo: "Agosto",
      folio: "9"
    });

    const decimales = container.querySelector(".rv-neto-decimales");
    expect(decimales?.textContent).toBe(".00");
  });
});
