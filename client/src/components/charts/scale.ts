// Marcas del eje en numeros redondos (0, 50 mil, 100 mil...) que cubren el
// maximo. Sin datos devuelve un eje de 0 a 1 para no dividir entre cero.
export function niceTicks(max: number, count = 4): number[] {
  if (!(max > 0)) return [0, 1];
  const rough = max / count;
  const magnitude = 10 ** Math.floor(Math.log10(rough));
  const step = [1, 2, 2.5, 5, 10].map((factor) => factor * magnitude).find((candidate) => candidate >= rough)!;
  const ticks: number[] = [];
  for (let value = 0; value < max + step; value += step) {
    ticks.push(Number(value.toFixed(10)));
    if (value >= max) break;
  }
  return ticks;
}

export function scaleLinear(domainMax: number, rangeStart: number, rangeEnd: number) {
  const span = domainMax || 1;
  return (value: number) => rangeStart + ((rangeEnd - rangeStart) * value) / span;
}

// Cada cuantas etiquetas del eje X pintar una para que no se encimen.
export function labelStride(count: number, width: number, minGap = 64): number {
  if (count <= 1) return 1;
  return Math.max(1, Math.ceil((count * minGap) / Math.max(width, 1)));
}
