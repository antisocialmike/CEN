import type { PayrollAnalytics } from "./ownerService";

export type PeriodPreset = "mes" | "trimestre" | "anio" | "12m";

export const PERIOD_PRESETS: { value: PeriodPreset; label: string }[] = [
  { value: "mes", label: "Este mes" },
  { value: "trimestre", label: "Este trimestre" },
  { value: "anio", label: "Este año" },
  { value: "12m", label: "Últimos 12 meses" }
];

export const DEFAULT_PRESET: PeriodPreset = "12m";

export function isPeriodPreset(value: string | null): value is PeriodPreset {
  return PERIOD_PRESETS.some((preset) => preset.value === value);
}

function iso(date: Date): string {
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

// Todos los presets terminan hoy: el periodo en curso cuenta aunque no haya cerrado.
export function resolvePreset(preset: PeriodPreset, today: Date): { from: string; to: string } {
  const year = today.getFullYear();
  const month = today.getMonth();
  const starts: Record<PeriodPreset, Date> = {
    mes: new Date(year, month, 1),
    trimestre: new Date(year, month - (month % 3), 1),
    anio: new Date(year, 0, 1),
    "12m": new Date(year, month - 11, 1)
  };
  return { from: iso(starts[preset]), to: iso(today) };
}

export function withoutEmptyCurrentMonth(
  analytics: PayrollAnalytics,
  today: Date
): PayrollAnalytics {
  const current = iso(new Date(today.getFullYear(), today.getMonth(), 1));
  const last = analytics.monthly[analytics.monthly.length - 1];
  if (analytics.monthly.length < 2 || last.month !== current || last.receipts > 0) {
    return analytics;
  }
  return {
    ...analytics,
    monthly: analytics.monthly.slice(0, -1),
    employer_cost: {
      ...analytics.employer_cost,
      monthly: analytics.employer_cost.monthly.filter((month) => month.month !== current)
    }
  };
}
