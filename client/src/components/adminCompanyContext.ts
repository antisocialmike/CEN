import { createContext, useContext } from "react";
import { AdminCompany } from "../services/adminCompanyService";

export interface AdminCompanyReady {
  status: "ready";
  companies: AdminCompany[];
  active: AdminCompany;
  choose: (id: number) => void;
}

export type AdminCompanyState = { status: "loading" } | AdminCompanyReady;

export const AdminCompanyContext = createContext<AdminCompanyState | null>(null);

// "none" fuera del panel de admin: los demas roles no eligen empresa.
export function useAdminCompanyStatus(): "none" | AdminCompanyState["status"] {
  return useContext(AdminCompanyContext)?.status ?? "none";
}

// Solo devuelve algo cuando ya hay empresa: la barra superior pinta el selector con esto.
export function useAdminCompany(): AdminCompanyReady | null {
  const state = useContext(AdminCompanyContext);
  return state?.status === "ready" ? state : null;
}

export function companyLabel(company: AdminCompany): string {
  return company.trade_name || company.legal_name;
}
