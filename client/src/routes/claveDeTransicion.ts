
const PANEL_ADMIN = ["/admin", "/admin/nomina", "/admin/usuarios"];
const PANEL_SUPERADMIN = ["/superadmin", "/superadmin/empresas"];
const PANEL_DUENO = ["/dueno", "/dueno/empresas"];

export function claveDeTransicion(ruta: string): string {
  if (PANEL_ADMIN.includes(ruta)) return "panel-admin";
  if (PANEL_SUPERADMIN.includes(ruta)) return "panel-superadmin";
  if (PANEL_DUENO.includes(ruta)) return "panel-dueno";
  return ruta;
}
