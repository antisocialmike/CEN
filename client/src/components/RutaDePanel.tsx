import { Suspense } from "react";
import { Outlet } from "react-router-dom";
import DashboardTopbar from "./DashboardTopbar";
import EsqueletoPanel from "./EsqueletoPanel";
import { getRole, UserRole } from "../services/authSession";
import { useAdminCompany, useAdminCompanyStatus } from "./adminCompanyContext";

const CONTEXTOS: Record<UserRole, string> = {
  superadmin: "Administración de la plataforma",
  owner: "Panel del dueño",
  admin: "Panel de administración",
  employee: "Portal del empleado"
};

export default function RutaDePanel() {
  const contexto = CONTEXTOS[getRole() ?? "employee"];
  const empresa = useAdminCompanyStatus();
  const empresaActiva = useAdminCompany()?.active.id;

  return (
    <div className="dashboard-shell">
      <a className="skip-link" href="#contenido">
        Ir al contenido
      </a>
      <DashboardTopbar context={contexto} />

      <main className="dashboard-content" id="contenido">
        {empresa === "loading" ? (
          <EsqueletoPanel />
        ) : (
          // La clave desmonta la pagina al cambiar de empresa: no queda estado de la anterior.
          <Suspense key={empresaActiva} fallback={<EsqueletoPanel />}>
            <Outlet />
          </Suspense>
        )}
      </main>
    </div>
  );
}
