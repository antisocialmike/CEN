import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import LandingPage from "./LandingPage";
import { desglosar } from "../components/landing/calculoNomina";

beforeAll(() => {
  vi.stubGlobal(
    "IntersectionObserver",
    class {
      constructor(private cb: IntersectionObserverCallback) {}
      observe(objetivo: Element) {
        this.cb(
          [{ target: objetivo, isIntersecting: true } as IntersectionObserverEntry],
          this as unknown as IntersectionObserver
        );
      }
      unobserve() {}
      disconnect() {}
      takeRecords() {
        return [];
      }
      root = null;
      rootMargin = "";
      thresholds = [];
    }
  );
});

afterEach(() => {
  delete document.documentElement.dataset.skin;
});

function montar() {
  return render(
    <MemoryRouter>
      <LandingPage />
    </MemoryRouter>
  );
}

describe("LandingPage", () => {
  it("activa el skin al montar y lo retira al desmontar", () => {
    const { unmount } = montar();
    expect(document.documentElement.dataset.skin).toBe("revolut");

    unmount();
    expect(document.documentElement.dataset.skin).toBeUndefined();
  });

  it("conserva las tres anclas del nav", () => {
    montar();
    for (const ancla of ["#calculo", "#roles", "#seguridad"]) {
      expect(document.querySelector(`a[href="${ancla}"]`)).not.toBeNull();
      expect(document.querySelector(ancla.replace("#", "#"))).not.toBeNull();
    }
  });

  it("el skip link apunta a un destino que existe y es enfocable", () => {
    montar();
    const skip = document.querySelector<HTMLAnchorElement>(".skip-link");
    expect(skip?.getAttribute("href")).toBe("#contenido");

    const destino = document.querySelector<HTMLElement>("#contenido");
    expect(destino).not.toBeNull();
    expect(destino!.tabIndex).toBe(-1);
  });

  it("la jerarquia de encabezados no salta niveles", () => {
    montar();
    const niveles = [...document.querySelectorAll("h1, h2, h3, h4")].map((h) =>
      Number(h.tagName[1])
    );

    expect(niveles[0]).toBe(1);
    for (let i = 1; i < niveles.length; i += 1) {
      expect(niveles[i] - niveles[i - 1]).toBeLessThanOrEqual(1);
    }
  });

  it("muestra cifras calculadas, no escritas a mano", () => {
    montar();
    const esperado = desglosar(22000, "mensual");

    const formato = new Intl.NumberFormat("es-MX", {
      style: "currency",
      currency: "MXN",
      minimumFractionDigits: 2
    });

    expect(screen.getAllByText(formato.format(esperado.isr)).length).toBeGreaterThan(0);
    expect(screen.getAllByText(formato.format(esperado.imss)).length).toBeGreaterThan(0);
    expect(screen.getAllByText(formato.format(esperado.neto)).length).toBeGreaterThan(0);
  });

  it("la calculadora recalcula al cambiar el sueldo", async () => {
    const { default: userEvent } = await import("@testing-library/user-event");
    const user = userEvent.setup();
    montar();

    const campo = screen.getByLabelText("Salario bruto");
    await user.clear(campo);
    await user.type(campo, "12000");

    const esperado = desglosar(12000, "mensual");
    const formato = new Intl.NumberFormat("es-MX", {
      style: "currency",
      currency: "MXN",
      minimumFractionDigits: 2
    });

    expect(
      screen.getAllByText(formato.format(esperado.isr)).length
    ).toBeGreaterThan(0);
  });

  it("declara el aviso de privacidad y los terminos sin inventar al responsable", () => {
    montar();

    const desplegables = [...document.querySelectorAll("summary")].map((s) =>
      s.textContent?.trim()
    );
    expect(desplegables).toEqual(["Aviso de privacidad", "Términos de uso"]);

    const enlacesPie = [...document.querySelectorAll('.rv-pie-links a')];
    expect(enlacesPie).toHaveLength(2);
    for (const enlace of enlacesPie) {
      expect(enlace.getAttribute("href")).toBe("#legal");
    }
    expect(document.querySelector("#legal")).not.toBeNull();

    expect(screen.getByText(/\[RAZÓN SOCIAL\]/)).toBeInTheDocument();
    expect(screen.getByText(/no es un CFDI/i)).toBeInTheDocument();
  });

  it("los cuatro marcadores del responsable siguen sin rellenar y a la vista", () => {
    montar();

    for (const marcador of [
      /\[RAZÓN SOCIAL\]/,
      /\[DOMICILIO FISCAL\]/,
      /\[CORREO PARA DERECHOS ARCO\]/,
      /\[CIUDAD DEL DOMICILIO\]/
    ]) {
      expect(screen.getByText(marcador)).toBeInTheDocument();
    }
  });

  it("el aviso declara la transferencia de correo, que si existe", () => {
    montar();
    expect(screen.getByText(/servidor SMTP de un proveedor externo/i)).toBeInTheDocument();
  });

  it("el aviso dice que el salario es dato patrimonial y exige consentimiento expreso", () => {
    montar();
    expect(screen.getByText(/consentimiento expreso, no tácito/i)).toBeInTheDocument();
  });

  it("el aviso afirma que no hay cookies, y eso tiene que seguir siendo cierto", () => {
    montar();
    expect(screen.getByText(/no usa cookies/i)).toBeInTheDocument();
  });
});

vi.mock("lenis", () => ({
  default: class {
    constructor() {
      throw new Error("lenis no pudo arrancar");
    }
  }
}));

describe("el scroll suave falla en silencio", () => {
  afterEach(() => {
    Reflect.deleteProperty(globalThis, "ResizeObserver");
  });

  it("sin ResizeObserver no intenta cargarlo", () => {
    expect(typeof ResizeObserver).toBe("undefined");

    expect(() => montar()).not.toThrow();
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
  });

  it("si lenis existe pero revienta, la pagina sigue en pie", async () => {
    vi.stubGlobal(
      "ResizeObserver",
      class {
        observe() {}
        unobserve() {}
        disconnect() {}
      }
    );

    const { unmount } = montar();
    await Promise.resolve();
    await Promise.resolve();

    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    expect(() => unmount()).not.toThrow();
  });
});
