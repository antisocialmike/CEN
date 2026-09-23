import { Suspense } from "react";
import { Outlet } from "react-router-dom";
import DashboardTopbar from "./DashboardTopbar";
import EsqueletoPanel from "./EsqueletoPanel";
import { getRole, UserRole } from "../services/authSession";

const CONTEXTOS: Record<UserRole, string> = {
  superadmin: "Administración de la plataforma",
  owner: "Panel del dueño",
  admin: "Panel de administración",
  employee: "Portal del empleado"
};

export default function RutaDePanel() {
  const contexto = CONTEXTOS[getRole() ?? "employee"];

  return (
    <div className="dashboard-shell">
      <a className="skip-link" href="#contenido">
        Ir al contenido
      </a>
      <DashboardTopbar context={contexto} />

      <main className="dashboard-content" id="contenido">
        <Suspense fallback={<EsqueletoPanel />}>
          <Outlet />
        </Suspense>
      </main>
    </div>
  );
}
