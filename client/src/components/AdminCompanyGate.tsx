import { ReactNode, useCallback, useEffect, useMemo, useState } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { Buildings } from "@phosphor-icons/react";
import ErrorMessage from "./ErrorMessage";
import { AdminCompany, listMyCompanies } from "../services/adminCompanyService";
import {
  clearActiveCompanyId,
  getActiveCompanyId,
  setActiveCompanyId
} from "../services/activeCompany";
import { logout } from "../services/authService";
import {
  AdminCompanyContext,
  AdminCompanyState,
  companyLabel,
  useAdminCompanyStatus
} from "./adminCompanyContext";

const LOADING: AdminCompanyState = { status: "loading" };

export default function AdminCompanyGate() {
  const navigate = useNavigate();
  const [companies, setCompanies] = useState<AdminCompany[] | null>(null);
  const [activeId, setActiveId] = useState<number | null>(getActiveCompanyId);
  const [failed, setFailed] = useState(false);

  const choose = useCallback((id: number) => {
    setActiveCompanyId(id);
    setActiveId(id);
  }, []);

  useEffect(() => {
    let isMounted = true;

    listMyCompanies()
      .then((list) => {
        if (!isMounted) return;
        setCompanies(list);
        if (list.length === 1) {
          choose(list[0].id);
        } else if (!list.some((company) => company.id === getActiveCompanyId())) {
          // La empresa guardada ya no se puede usar: le quitaron el acceso o se desactivo.
          clearActiveCompanyId();
          setActiveId(null);
        }
      })
      .catch(() => isMounted && setFailed(true));

    return () => {
      isMounted = false;
    };
  }, [choose]);

  const active = companies?.find((company) => company.id === activeId);
  const value = useMemo<AdminCompanyState | null>(() => {
    if (companies === null) return LOADING;
    return active ? { status: "ready", companies, active, choose } : null;
  }, [companies, active, choose]);

  if (failed) {
    return (
      <GateCard title="No pudimos cargar tus empresas">
        <ErrorMessage message="Revisa tu conexión y recarga la página." />
      </GateCard>
    );
  }

  if (companies !== null && companies.length === 0) {
    return (
      <GateCard title="No administras ninguna empresa activa">
        <p className="auth-card-subtitle">
          Pide al dueño de la empresa que te vuelva a asignar. Mientras tanto no hay nómina que operar.
        </p>
        <button
          className="btn btn-line btn-block"
          onClick={() => {
            logout();
            navigate("/login", { replace: true });
          }}
        >
          Cerrar sesión
        </button>
      </GateCard>
    );
  }

  if (companies !== null && value === null) {
    return (
      <GateCard title="¿Con qué empresa vas a trabajar?">
        <p className="auth-card-subtitle">
          Administras varias. Todo lo que hagas se guardará en la que elijas; puedes cambiarla
          desde la barra superior.
        </p>
        <ul className="company-choice-list">
          {companies.map((company) => (
            <li key={company.id}>
              <button className="btn btn-line btn-block" onClick={() => choose(company.id)}>
                <Buildings weight="bold" />
                {companyLabel(company)}
              </button>
            </li>
          ))}
        </ul>
      </GateCard>
    );
  }

  return (
    // Mientras carga, las rutas pintan su propio armazon con su esqueleto.
    <AdminCompanyContext.Provider value={value}>
      <Outlet />
    </AdminCompanyContext.Provider>
  );
}

// Para las pantallas de admin que no viven dentro del armazon del panel.
export function AdminCompanyReadyPage() {
  if (useAdminCompanyStatus() === "loading") {
    return (
      <GateCard title="Un momento">
        <p className="auth-card-subtitle" role="status">
          Cargando tus empresas…
        </p>
      </GateCard>
    );
  }
  return <Outlet />;
}

function GateCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="signup-page">
      <main className="signup-card">
        <h1 className="auth-card-title">{title}</h1>
        {children}
      </main>
    </div>
  );
}
