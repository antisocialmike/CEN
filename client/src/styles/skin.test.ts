import { readdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const ARCHIVOS = ["src/styles/skin-base.css", "src/styles/skin-landing.css"];

const css = ARCHIVOS.map((f) => readFileSync(resolve(process.cwd(), f), "utf8")).join("\n");

const sinComentarios = css.replace(/\/\*[\s\S]*?\*\//g, "");

interface Bloque {
  prelude: string;
  cuerpo: string;
}

function bloques(fuente: string): Bloque[] {
  const salida: Bloque[] = [];
  let profundidad = 0;
  let prelude = "";
  let inicioCuerpo = 0;

  for (let i = 0; i < fuente.length; i += 1) {
    const c = fuente[i];
    if (c === "{") {
      if (profundidad === 0) inicioCuerpo = i + 1;
      profundidad += 1;
    } else if (c === "}") {
      profundidad -= 1;
      if (profundidad === 0) {
        salida.push({ prelude: prelude.trim(), cuerpo: fuente.slice(inicioCuerpo, i) });
        prelude = "";
      }
    } else if (profundidad === 0) {
      prelude += c;
    }
  }

  return salida.filter((b) => b.prelude);
}

const ENVOLVENTE = /^@(media|container|supports|layer)\b/i;

function preludesQueDebenLlevarPrefijo(fuente: string): string[] {
  return bloques(fuente).flatMap((b) =>
    ENVOLVENTE.test(b.prelude) ? preludesQueDebenLlevarPrefijo(b.cuerpo) : [b.prelude]
  );
}

describe("el contrato de temas se mantiene", () => {
  const selectores = preludesQueDebenLlevarPrefijo(sinComentarios);

  it("encuentra reglas que analizar", () => {
    expect(selectores.length).toBeGreaterThan(0);
  });

  it("declara color-scheme en los tres bloques que exige el selector de tema", () => {
    expect(sinComentarios).toMatch(/:root\s*\{[^}]*color-scheme:\s*light dark/);
    expect(sinComentarios).toMatch(
      /:root\[data-theme="light"\]\s*\{[^}]*color-scheme:\s*light/
    );
    expect(sinComentarios).toMatch(
      /:root\[data-theme="dark"\]\s*\{[^}]*color-scheme:\s*dark/
    );
  });

  it("define cada color con light-dark(), nunca dentro de @media ni [data-theme]", () => {
    expect(sinComentarios).not.toMatch(/@media[^{]*prefers-color-scheme/);

    const bloquesTema = selectores.filter((s) => s.includes("[data-theme="));
    expect(bloquesTema).toEqual([
      ':root[data-theme="light"]',
      ':root[data-theme="dark"]',
    ]);
  });
});

function declaracionesDirectas(cuerpo: string): string[] {
  let plano = "";
  let profundidad = 0;

  for (const c of cuerpo) {
    if (c === "{") {
      profundidad += 1;
      continue;
    }
    if (c === "}") {
      profundidad -= 1;
      continue;
    }
    if (profundidad === 0) plano += c;
  }

  return plano
    .split(";")
    .map((d) => d.trim())
    .filter(Boolean);
}

function reglasConContexto(
  fuente: string,
  pila: string[] = []
): { prelude: string; declaraciones: string[]; pila: string[] }[] {
  return bloques(fuente).flatMap((b) => {
    const nueva = ENVOLVENTE.test(b.prelude) ? [...pila, b.prelude] : pila;

    return [
      { prelude: b.prelude, declaraciones: declaracionesDirectas(b.cuerpo), pila: nueva },
      ...(b.cuerpo.includes("{") ? reglasConContexto(b.cuerpo, nueva) : []),
    ];
  });
}

describe("el revelado ligado al scroll no puede dejar contenido invisible", () => {
  const reglas = reglasConContexto(sinComentarios);

  const ligadasAlScroll = reglas.filter((r) =>
    r.declaraciones.some((d) => /^animation-timeline\s*:/.test(d))
  );

  const ocultan = new Set(
    [...sinComentarios.matchAll(/@keyframes\s+(rv-[a-z0-9-]+)\s*\{([\s\S]*?)\n\}/g)]
      .filter(([, , cuerpo]) =>
        /opacity:\s*0\b|clip-path:\s*inset\([^)]*100%/.test(cuerpo)
      )
      .map(([, nombre]) => nombre)
  );

  it("hay reglas ligadas al scroll y keyframes que ocultan que analizar", () => {
    expect(ligadasAlScroll.length).toBeGreaterThan(0);
    expect(ocultan.size).toBeGreaterThan(0);
  });

  it("toda animation-timeline vive bajo @supports", () => {
    const huerfanas = ligadasAlScroll.filter(
      (r) => !r.pila.some((a) => /^@supports[^{]*animation-timeline/i.test(a))
    );

    expect(
      huerfanas.map((r) => r.prelude),
      "Reglas sin @supports (animation-timeline: ...) por encima"
    ).toEqual([]);
  });

  it("todo revelado que oculta y depende del scroll respeta prefers-reduced-motion", () => {
    const desprotegidas = ligadasAlScroll.filter((r) => {
      const esconde = r.declaraciones.some((d) => {
        const nombre = /^animation(?:-name)?\s*:\s*([a-z0-9-]+)/i.exec(d)?.[1];
        return nombre ? ocultan.has(nombre) : false;
      });

      if (!esconde) return false;

      return !r.pila.some((a) =>
        /prefers-reduced-motion\s*:\s*no-preference/i.test(a)
      );
    });

    expect(
      desprotegidas.map((r) => r.prelude),
      "Reglas que ocultan contenido y dependen del scroll sin la guarda de movimiento reducido"
    ).toEqual([]);
  });
});

describe("el alto del nav movil cuadra con sus partes", () => {
  const numero = (re: RegExp, donde: string, que: string) => {
    const m = re.exec(donde);
    if (!m) throw new Error(`no encuentro ${que}`);
    return Number(m[1]);
  };

  it("--rv-nav-alto en moviles es la suma de padding, filas, separacion y borde", () => {
    const bloque = /@media\s*\(max-width:\s*768px\)\s*\{([\s\S]*?)\n\}/.exec(sinComentarios)?.[1];
    expect(bloque, "no encuentro el @media de 768px").toBeTruthy();

    const declarado = numero(
      /--rv-nav-alto\s*:\s*(\d+)px/,
      bloque!,
      "--rv-nav-alto dentro del @media de 768px"
    );

    const padding = numero(
      /--rv-p-espacio-2\s*:\s*(\d+)px/,
      sinComentarios,
      "el token --rv-p-espacio-2"
    );
    const separacion = padding;
    const toque = numero(
      /--rv-toque-min\s*:\s*(\d+)px/,
      sinComentarios,
      "el token --rv-toque-min"
    );
    const borde = 1;

    const temaCss = readFileSync(resolve(process.cwd(), "src/styles/theme.css"), "utf8");
    const altoBoton = numero(
      /\.btn\s*\{[^}]*?min-height:\s*(\d+)px/,
      temaCss,
      "el min-height de .btn en theme.css"
    );

    const suma = padding * 2 + altoBoton + separacion + toque + borde;

    expect(
      declarado,
      `--rv-nav-alto dice ${declarado}px pero las partes suman ${suma}px ` +
        `(${padding} + ${altoBoton} + ${separacion} + ${toque} + ${padding} + ${borde}). ` +
        "Si cambiaste alguna, actualiza el token o las anclas aterrizan bajo el nav."
    ).toBe(suma);
  });
});

describe("el orden de carga de las hojas", () => {
  const main = readFileSync(resolve(process.cwd(), "src/main.tsx"), "utf8");

  const posicion = (aguja: string) => {
    const i = main.indexOf(aguja);
    if (i === -1) throw new Error(`no encuentro "${aguja}" en main.tsx`);
    return i;
  };

  it("theme.css va antes que skin-base.css, para que el skin gane los empates", () => {
    expect(posicion('"./styles/theme.css"')).toBeLessThan(
      posicion('"./styles/skin-base.css"')
    );
  });

  it("las dos hojas van antes de importar App", () => {
    const app = posicion('from "./App"');

    expect(posicion('"./styles/theme.css"')).toBeLessThan(app);
    expect(posicion('"./styles/skin-base.css"')).toBeLessThan(app);
  });

  it("nadie mas importa esas dos hojas", () => {
    const fuentes = readdirSync(resolve(process.cwd(), "src"), {
      recursive: true,
      encoding: "utf8"
    }).filter((f) => /\.tsx?$/.test(f) && !f.endsWith("main.tsx"));

    const culpables = fuentes.filter((f) => {
      const texto = readFileSync(resolve(process.cwd(), "src", f), "utf8");
      return /^\s*import\s+["'][^"']*styles\/(theme|skin-base)\.css["']/m.test(texto);
    });

    expect(
      culpables,
      "Estas hojas solo puede importarlas main.tsx; ver el comentario de arriba"
    ).toEqual([]);
  });
});

describe("el neto se pinta con su propio token", () => {
  const tema = readFileSync(resolve(process.cwd(), "src/styles/theme.css"), "utf8");
  const temaSinComentarios = tema.replace(/\/\*[\s\S]*?\*\//g, "");

  function declaracion(selector: string, propiedad: string): string | undefined {
    const bloque = bloques(temaSinComentarios).find(
      (b) => b.prelude.trim() === selector
    );
    return bloque?.cuerpo
      .split(";")
      .map((d) => d.trim())
      .find((d) => d.startsWith(`${propiedad}:`))
      ?.slice(propiedad.length + 1)
      .trim();
  }

  it("`--neto` sale del token del skin y no de un color suelto", () => {
    expect(sinComentarios).toMatch(/--neto:\s*var\(--rv-neto\)\s*;/);
  });

  it.each([
    [".receipt-card-net", "la tarjeta del historial"],
    [".payroll-result-row.total span:last-child", "el 'Neto a pagar' del panel"],
    [".stat-card-value.is-neto", "el 'Ultimo neto recibido' del resumen"]
  ])("%s pide var(--neto) — %s", (selector) => {
    expect(declaracion(selector, "color")).toBe("var(--neto)");
  });

  it("alguien usa de verdad la clase `is-neto`", () => {
    const fuentes = readdirSync(resolve(process.cwd(), "src"), {
      recursive: true,
      encoding: "utf8"
    }).filter((f) => /\.tsx$/.test(f));

    const quienes = fuentes.filter((f) =>
      /className="[^"]*\bis-neto\b/.test(
        readFileSync(resolve(process.cwd(), "src", f), "utf8")
      )
    );

    expect(quienes.length, "nadie pide is-neto; la regla quedo muerta")
      .toBeGreaterThan(0);
  });

  it("la columna de la tabla se queda en tinta", () => {
    expect(declaracion(".data-table .net", "color")).toBe("var(--ink)");
  });
});
