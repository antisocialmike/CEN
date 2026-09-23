
const PANEL_ADMIN = ["/admin", "/admin/empleados"];
const PANEL_SUPERADMIN = ["/superadmin", "/superadmin/empresas"];

export function claveDeTransicion(ruta: string): string {
  if (PANEL_ADMIN.includes(ruta)) return "panel-admin";
  if (PANEL_SUPERADMIN.includes(ruta)) return "panel-superadmin";
  return ruta;
}
