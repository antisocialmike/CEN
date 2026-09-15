
const PANEL_ADMIN = ["/admin", "/admin/empleados"];

export function claveDeTransicion(ruta: string): string {
  return PANEL_ADMIN.includes(ruta) ? "panel-admin" : ruta;
}
