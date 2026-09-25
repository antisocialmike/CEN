// La empresa con la que trabaja el admin vive en sessionStorage y no en
// localStorage: cada pestaña lleva la suya. Con localStorage, cambiar de empresa
// en una pestaña haria que la otra siguiera escribiendo nomina, sin avisar, en
// la empresa nueva.
const ACTIVE_COMPANY_KEY = "cen_active_company";

export const COMPANY_HEADER = "X-Company-Id";

export function getActiveCompanyId(): number | null {
  try {
    const raw = sessionStorage.getItem(ACTIVE_COMPANY_KEY);
    const id = raw === null ? NaN : Number(raw);
    return Number.isInteger(id) && id > 0 ? id : null;
  } catch {
    return null;
  }
}

export function setActiveCompanyId(id: number): void {
  try {
    sessionStorage.setItem(ACTIVE_COMPANY_KEY, String(id));
  } catch {
    // Sin almacenamiento la eleccion dura lo que dure la pagina; el portero
    // la vuelve a pedir al recargar.
  }
}

export function clearActiveCompanyId(): void {
  try {
    sessionStorage.removeItem(ACTIVE_COMPANY_KEY);
  } catch {
    // Nada que limpiar si el navegador no deja tocar el almacenamiento.
  }
}
