import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const leer = (archivo: string) => readFileSync(resolve(process.cwd(), archivo), "utf8");

const scriptsEnLinea = [...leer("index.html").matchAll(/<script>([\s\S]*?)<\/script>/g)].map(
  (coincidencia) => coincidencia[1]
);
const nginx = leer("nginx.conf");
const politicas = [...nginx.matchAll(/add_header Content-Security-Policy "([^"]+)"/g)].map(
  (coincidencia) => coincidencia[1]
);

describe("la CSP del nginx", () => {
  it("va en cada bloque que pone cabeceras de seguridad", () => {
    const bloquesConCabeceras = nginx.match(/add_header X-Frame-Options/g) ?? [];
    expect(politicas).toHaveLength(bloquesConCabeceras.length);
    expect(new Set(politicas).size).toBe(1);
  });

  it("autoriza cada script en linea de index.html por su hash", () => {
    expect(scriptsEnLinea.length).toBeGreaterThan(0);
    for (const script of scriptsEnLinea) {
      const hash = createHash("sha256").update(script).digest("base64");
      expect(politicas[0]).toContain(`'sha256-${hash}'`);
    }
  });

  it("no abre la puerta a scripts en linea ni a eval", () => {
    const scriptSrc = politicas[0].match(/script-src ([^;]+)/)?.[1] ?? "";
    expect(scriptSrc).not.toContain("'unsafe-inline'");
    expect(politicas[0]).not.toContain("'unsafe-eval'");
  });

  it("deja hablar al navegador con la API que se fija al construir", () => {
    expect(politicas[0]).toMatch(/connect-src 'self' __API_ORIGIN__;/);
  });
});
