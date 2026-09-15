import { mkdirSync, existsSync, statSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const AQUI = dirname(fileURLToPath(import.meta.url));
const DESTINO = join(AQUI, "..", "public", "fuentes");
const CSS_FONTSHARE = "https://api.fontshare.com/v2/css?f%5B%5D=satoshi@400,500,700&display=swap";

const PESOS = [400, 500, 700];
const nombre = (peso) => `satoshi-${peso}.woff2`;
const MINIMO = 10_000;

const obligatorio = process.argv.includes("--obligatorio");

function yaEstan() {
  return PESOS.every((p) => {
    const ruta = join(DESTINO, nombre(p));
    return existsSync(ruta) && statSync(ruta).size > MINIMO;
  });
}

function extraeUrls(css) {
  const urls = new Map();
  for (const bloque of css.split("@font-face").slice(1)) {
    const familia = bloque.match(/font-family:\s*'([^']+)'/)?.[1];
    if (familia !== "Satoshi") continue;
    const peso = Number(bloque.match(/font-weight:\s*(\d+)/)?.[1]);
    const url = bloque.match(/url\('([^']+\.woff2)'\)/)?.[1];
    if (peso && url) urls.set(peso, url.startsWith("//") ? "https:" + url : url);
  }
  return urls;
}

async function bajaUno(peso, url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url} respondio ${r.status}`);
  const datos = Buffer.from(await r.arrayBuffer());
  if (datos.subarray(0, 4).toString("ascii") !== "wOF2") {
    throw new Error(`lo descargado para el peso ${peso} no es un woff2`);
  }
  if (datos.length < MINIMO) {
    throw new Error(`el archivo del peso ${peso} pesa solo ${datos.length} bytes`);
  }
  writeFileSync(join(DESTINO, nombre(peso)), datos);
  return datos.length;
}

async function principal() {
  mkdirSync(DESTINO, { recursive: true });

  if (yaEstan()) {
    console.log("fuentes: Satoshi ya esta en public/fuentes, no bajo nada");
    return;
  }

  console.log("fuentes: bajando Satoshi de Fontshare…");
  const respuesta = await fetch(CSS_FONTSHARE);
  if (!respuesta.ok) throw new Error(`el CSS de Fontshare respondio ${respuesta.status}`);

  const urls = extraeUrls(await respuesta.text());
  const faltan = PESOS.filter((p) => !urls.has(p));
  if (faltan.length) throw new Error(`Fontshare no devolvio los pesos ${faltan.join(", ")}`);

  for (const peso of PESOS) {
    const bytes = await bajaUno(peso, urls.get(peso));
    console.log(`  ${nombre(peso)}  ${bytes} bytes`);
  }
}

try {
  await principal();
} catch (error) {
  const aviso = `fuentes: no pude dejar Satoshi lista (${error.message})`;
  if (obligatorio) {
    console.error(`${aviso}.\nSin ella el sitio cae a Helvetica en las nueve rutas, asi que paro aqui.`);
    process.exit(1);
  }
  console.warn(`${aviso}. Sigo, pero ejecuta "pnpm fuentes" antes de construir.`);
}
