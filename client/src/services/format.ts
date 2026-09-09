const currency = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  minimumFractionDigits: 2
});

const monthLong = new Intl.DateTimeFormat("es-MX", { month: "long", year: "numeric" });
const dayLong = new Intl.DateTimeFormat("es-MX", {
  day: "numeric",
  month: "long",
  year: "numeric"
});
const dayShort = new Intl.DateTimeFormat("es-MX", { day: "2-digit", month: "short" });

function toLocalDate(value: string): Date {
  return new Date(/^\d{4}-\d{2}-\d{2}$/.test(value) ? `${value}T00:00:00` : value);
}

function capitalize(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export function formatCurrency(value: number): string {
  return currency.format(value);
}

export function formatMonth(value: string): string {
  return capitalize(monthLong.format(toLocalDate(value)));
}

export function formatDate(value: string): string {
  return capitalize(dayLong.format(toLocalDate(value)));
}

export function formatDateShort(value: string): string {
  return dayShort.format(toLocalDate(value)).replace(/-/g, " ").replace(/\./g, "");
}

export function currentPeriod(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

export function formatRange(startValue: string, endValue: string): string {
  const start = toLocalDate(startValue);
  const end = toLocalDate(endValue);
  const sameMonth = start.getMonth() === end.getMonth();

  return sameMonth
    ? `${start.getDate()} al ${dayLong.format(end)}`
    : `${dayLong.format(start)} al ${dayLong.format(end)}`;
}

export function periodStartsOf(periodicity: string, month: string): string[] {
  const [year, monthNumber] = month.split("-").map(Number);
  const lastDay = new Date(year, monthNumber, 0).getDate();
  const pad = (day: number) => String(day).padStart(2, "0");

  if (periodicity === "mensual") {
    return [`${month}-01`];
  }

  if (periodicity === "quincenal") {
    return [`${month}-01`, `${month}-16`];
  }

  const starts: string[] = [];
  for (let day = 1; day <= lastDay; day += 7) {
    starts.push(`${month}-${pad(day)}`);
  }
  return starts;
}
