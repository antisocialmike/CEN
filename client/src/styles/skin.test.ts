/// <reference types="node" />
// Esta primera linea NO es un comentario: es una directiva de TypeScript que
// trae los globales de node (process, node:fs) solo para este archivo, sin
// exponerlos al resto de src/. Sin ella, `pnpm typecheck` falla con cuatro
// errores TS2591.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const PREFIJO = ':root[data-skin="revolut"]';

/* El skin vive en dos archivos desde que se partio: skin-base.css lleva los
   tokens y la capa puente y lo carga main.tsx para toda la app, y
   skin-landing.css lleva las secciones y se queda en el chunk lazy. La guardia
   tiene que cubrir los dos, porque el de base es justamente el que puede
   filtrarse a las otras ocho rutas. Se analizan juntos para que las reglas que
   cruzan de archivo —el alto del nav movil usa tokens de base— sigan cuadrando. */
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

function selectoresDe(lista: string): string[] {
  const partes: string[] = [];
  let profundidad = 0;
  let actual = "";

  for (const c of lista) {
    if (c === "(") profundidad += 1;
    else if (c === ")") profundidad -= 1;

    if (c === "," && profundidad === 0) {
      partes.push(actual.trim());
      actual = "";
    } else {
      actual += c;
    }
  }

  partes.push(actual.trim());
  return partes.filter(Boolean);
}

describe("el skin no puede filtrarse a las otras rutas", () => {
  const selectores = preludesQueDebenLlevarPrefijo(sinComentarios);

  it("encuentra reglas que analizar", () => {
    expect(selectores.length).toBeGreaterThan(0);
  });

  it("toda regla de nivel superior arranca con el prefijo del skin", () => {
    const infractores = selectores.filter((selector) => {
      if (/^@property\s+--rv-[a-z0-9-]+$/i.test(selector)) return false;
      if (/^@keyframes\s+rv-[a-z0-9-]+$/i.test(selector)) return false;

      return !selectoresDe(selector).every((parte) => parte.startsWith(PREFIJO));
    });

    expect(
      infractores,
      `Reglas sin el prefijo ${PREFIJO}:\n  ${infractores.join("\n  ")}`
    ).toEqual([]);
  });

  it("no redefine tokens fuera del skin ni toca body o html sueltos", () => {
    expect(sinComentarios).not.toMatch(/(^|\})\s*:root\s*\{/);
    expect(sinComentarios).not.toMatch(/(^|\})\s*(body|html|\*)\s*[,{]/);
  });

  it("declara color-scheme en los tres bloques que exige el selector de tema", () => {
    expect(sinComentarios).toMatch(
      /:root\[data-skin="revolut"\]\s*\{[^}]*color-scheme:\s*light dark/
    );
    expect(sinComentarios).toMatch(
      /:root\[data-skin="revolut"\]\[data-theme="light"\]\s*\{[^}]*color-scheme:\s*light/
    );
    expect(sinComentarios).toMatch(
      /:root\[data-skin="revolut"\]\[data-theme="dark"\]\s*\{[^}]*color-scheme:\s*dark/
    );
  });

  it("define cada color con light-dark(), nunca dentro de @media ni [data-theme]", () => {
    expect(sinComentarios).not.toMatch(/@media[^{]*prefers-color-scheme/);

    const bloquesTema = selectores.filter((s) => s.includes("[data-theme="));
    expect(bloquesTema).toEqual([
      ':root[data-skin="revolut"][data-theme="light"]',
      ':root[data-skin="revolut"][data-theme="dark"]',
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
