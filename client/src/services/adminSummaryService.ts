import httpClient from "./httpClient";
import { TipoRegimen } from "./employeeService";

export interface AdminSummary {
  // El primer dia del mes en curso: los pendientes se cuentan contra este mes.
  month: string;
  // Activos y con salario: las personas que ofrece la calculadora.
  on_payroll: number;
  pending: {
    total: number;
    // Solo los primeros; `total` dice cuantos faltan en realidad.
    people: { id: number; name: string; tipo_regimen: TipoRegimen }[];
  };
  // null si la empresa todavia no emite ningun recibo.
  last_month: {
    month: string;
    gross_payroll: number;
    net_paid: number;
    isr_withheld: number;
    imss_withheld: number;
    receipts: number;
    paid_people: number;
  } | null;
  movements: { id: number; name: string; kind: "alta" | "baja"; happened_at: string }[];
  regimes: { tipo_regimen: TipoRegimen; people: number }[];
}

// La empresa la pone httpClient en la cabecera; el servidor la valida.
export async function getAdminSummary(): Promise<AdminSummary> {
  const response = await httpClient.get<AdminSummary>("/admin/summary");
  return response.data;
}
