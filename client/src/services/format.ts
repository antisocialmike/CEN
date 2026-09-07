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

function capitalize(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export function formatCurrency(value: number): string {
  return currency.format(value);
}

export function formatMonth(value: string): string {
  return capitalize(monthLong.format(new Date(value)));
}

export function formatDate(value: string): string {
  return capitalize(dayLong.format(new Date(value)));
}

export function formatDateShort(value: string): string {
  return dayShort.format(new Date(value)).replace(/-/g, " ").replace(/\./g, "");
}
