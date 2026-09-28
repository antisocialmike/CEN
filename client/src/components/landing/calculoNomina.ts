
export type Periodicidad = "mensual" | "quincenal" | "semanal";

// Parametros de 2026 (febrero a diciembre). En el producto llegan de la base con
// su vigencia; aqui son fijos porque la landing solo enseña un ejemplo del año.
const UMA_DIARIA = 117.31;
const UMA_MENSUAL = 3566.22;
const SALARIO_MINIMO = 315.04;
const DIAS_TARIFA_MENSUAL = 30.4;

// El salario diario se saca con 30, 15 o 7 dias, como en el servidor.
const DIAS_NOMINALES: Record<Periodicidad, number> = {
  mensual: 30,
  quincenal: 15,
  semanal: 7
};

// Primer año de antigüedad: (365 + 15 de aguinaldo + 12 de vacaciones x 25%) / 365.
const FACTOR_INTEGRACION = 1.049315;

const TARIFA_DIAS: Record<Periodicidad, number> = {
  mensual: 30.4,
  quincenal: 15.2,
  semanal: 7.0
};

export const ETIQUETA_PERIODICIDAD: Record<Periodicidad, string> = {
  mensual: "Mensual",
  quincenal: "Quincenal",
  semanal: "Semanal"
};

const ISR_SUBSIDIO_LIMITE = 11492.66;
// 15.02% de la UMA mensual: 535.65.
const ISR_SUBSIDIO_MONTO = redondear(UMA_MENSUAL * 0.1502);

const ISR_TABLA: [number, number | null, number, number][] = [
  [0.0, 844.59, 0.0, 0.0192],
  [844.6, 7168.51, 16.22, 0.064],
  [7168.52, 12598.02, 420.95, 0.1088],
  [12598.03, 14644.64, 1011.68, 0.16],
  [14644.65, 17533.64, 1339.14, 0.1792],
  [17533.65, 35362.83, 1856.84, 0.2136],
  [35362.84, 55736.68, 5665.16, 0.2352],
  [55736.69, 106410.5, 10457.09, 0.3],
  [106410.51, 141880.66, 25659.23, 0.32],
  [141880.67, 425641.99, 37009.69, 0.34],
  [425642.0, null, 133488.54, 0.35]
];

const IMSS_ENFERMEDAD_MATERNIDAD_DINERO = 0.0025;
const IMSS_GASTOS_MEDICOS_PENSIONADOS = 0.00375;
const IMSS_INVALIDEZ_VIDA = 0.00625;
const IMSS_CESANTIA_EDAD_AVANZADA_VEJEZ = 0.01125;
const IMSS_ENFERMEDAD_MATERNIDAD_EXCEDENTE = 0.004;
const IMSS_TOPE_UMA = 25;
const IMSS_UMBRAL_EXCEDENTE_UMA = 3;

function redondear(importe: number): number {
  return Math.round(importe * 100) / 100;
}

function salarioDiario(bruto: number, periodicidad: Periodicidad): number {
  return redondear(bruto / DIAS_NOMINALES[periodicidad]);
}

// A quien gana el minimo no se le retiene ISR (LISR art. 96) y su IMSS lo paga
// el patron (LSS art. 36).
function ganaElMinimo(bruto: number, periodicidad: Periodicidad): boolean {
  return salarioDiario(bruto, periodicidad) <= SALARIO_MINIMO;
}

// Salario base de cotizacion: el diario integrado, entre el minimo y 25 UMA.
function salarioBaseDeCotizacion(bruto: number, periodicidad: Periodicidad): number {
  const integrado = salarioDiario(bruto, periodicidad) * FACTOR_INTEGRACION;
  return redondear(Math.min(Math.max(integrado, SALARIO_MINIMO), UMA_DIARIA * IMSS_TOPE_UMA));
}

function factorDe(periodicidad: Periodicidad): number {
  return TARIFA_DIAS[periodicidad] / DIAS_TARIFA_MENSUAL;
}

export function calcularISR(bruto: number, periodicidad: Periodicidad = "mensual"): number {
  if (ganaElMinimo(bruto, periodicidad)) return 0;

  const factor = factorDe(periodicidad);
  let causado = 0;

  for (const [inferior, superior, cuotaFija, porcentaje] of ISR_TABLA) {
    const li = inferior * factor;
    const ls = superior === null ? null : superior * factor;
    const dentroDelRango = bruto >= li && (ls === null || bruto <= ls);

    if (dentroDelRango) {
      causado = cuotaFija * factor + (bruto - li) * porcentaje;
      break;
    }
  }

  if (bruto <= ISR_SUBSIDIO_LIMITE * factor) {
    causado = Math.max(0, causado - ISR_SUBSIDIO_MONTO * factor);
  }

  return redondear(causado);
}

// Cuota obrera: el SBC por los dias del periodo, como en el servidor.
export function calcularIMSS(bruto: number, periodicidad: Periodicidad = "mensual"): number {
  if (ganaElMinimo(bruto, periodicidad)) return 0;

  const sbc = salarioBaseDeCotizacion(bruto, periodicidad);
  const dias = DIAS_NOMINALES[periodicidad];
  const excedente = Math.max(0, sbc - UMA_DIARIA * IMSS_UMBRAL_EXCEDENTE_UMA);

  const cuotasSobreSBC =
    IMSS_ENFERMEDAD_MATERNIDAD_DINERO +
    IMSS_GASTOS_MEDICOS_PENSIONADOS +
    IMSS_INVALIDEZ_VIDA +
    IMSS_CESANTIA_EDAD_AVANZADA_VEJEZ;

  const imss =
    sbc * dias * cuotasSobreSBC + excedente * dias * IMSS_ENFERMEDAD_MATERNIDAD_EXCEDENTE;

  return redondear(imss);
}

export interface Desglose {
  bruto: number;
  isr: number;
  imss: number;
  neto: number;
  periodicidad: Periodicidad;
}

export function desglosar(bruto: number, periodicidad: Periodicidad = "mensual"): Desglose {
  const limpio = Number.isFinite(bruto) && bruto > 0 ? bruto : 0;
  const isr = calcularISR(limpio, periodicidad);
  const imss = calcularIMSS(limpio, periodicidad);

  return {
    bruto: redondear(limpio),
    isr,
    imss,
    neto: redondear(limpio - isr - imss),
    periodicidad
  };
}
