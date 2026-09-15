import { Suspense } from "react";
import { Outlet } from "react-router-dom";
import DashboardTopbar from "./DashboardTopbar";
import EsqueletoPanel from "./EsqueletoPanel";
import { getRole } from "../services/authSession";

export default function RutaDePanel() {
  const contexto =
    getRole() === "admin" ? "Panel de administración" : "Portal del empleado";

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
