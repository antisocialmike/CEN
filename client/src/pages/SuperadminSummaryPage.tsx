import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import { Buildings, UserCirclePlus, UsersThree } from "@phosphor-icons/react";
import { blockVariants, stackVariants, useStill } from "../motion/variants";
import ErrorMessage from "../components/ErrorMessage";
import Skeleton from "../components/Skeleton";
import StackedColumnChart from "../components/charts/StackedColumnChart";
import ChartTable from "../components/charts/ChartTable";
import { getPlatformSummary, PlatformSummary } from "../services/superadminService";
import { formatDateShort, formatInteger, formatMonth, formatMonthShort } from "../services/format";
import "../styles/skin-dueno.css";

const SIGNUP_SERIES = [
  { key: "companies", name: "Empresas", color: "var(--viz-percepcion)" },
  { key: "owners", name: "Dueños", color: "var(--viz-imss)" }
];

// Las acciones que escribe company_repository en platform_audit_log.
const ACTION_LABELS: Record<string, string> = {
  "owner.create": "Alta de dueño",
  "owner.update": "Cambio de datos del dueño",
  "owner.activate": "Reactivación de dueño",
  "owner.deactivate": "Baja de dueño",
  "owner.reset_password": "Contraseña temporal del dueño",
  "company.create": "Alta de empresa",
  "company.update": "Cambio de datos de la empresa",
  "company.activate": "Reactivación de empresa",
  "company.deactivate": "Baja de empresa",
  "company.risk_premium": "Prima de riesgo de trabajo",
  "company.invite_admin": "Invitación de administrador",
  "company.assign_admin": "Asignación de administrador",
  "company.unassign_admin": "Retiro de administrador",
  "company.assign_owner": "Asignación de dueño",
  "company.unassign_owner": "Retiro de dueño"
};

function actionLabel(action: string): string {
  return ACTION_LABELS[action] ?? action;
}

function plural(count: number, one: string, many: string): string {
  return `${formatInteger(count)} ${count === 1 ? one : many}`;
}

export default function SuperadminSummaryPage() {
  const stackTravel = useStill(stackVariants);
  const blockTravel = useStill(blockVariants);
  const navigate = useNavigate();
  const [summary, setSummary] = useState<PlatformSummary | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let isMounted = true;

    getPlatformSummary()
      .then((data) => isMounted && setSummary(data))
      .catch(() => isMounted && setFailed(true));

    return () => {
      isMounted = false;
    };
  }, []);

  const isEmpty =
    summary !== null &&
    summary.companies.active + summary.companies.inactive === 0 &&
    summary.users.owner.active + summary.users.owner.inactive === 0;
  const hiddenOrphans = summary
    ? summary.orphaned.total - summary.orphaned.companies.length
    : 0;
  const cards = summary
    ? [
        {
          label: "Empresas activas",
          count: summary.companies.active,
          detail: plural(summary.companies.inactive, "inactiva", "inactivas")
        },
        {
          label: "Dueños activos",
          count: summary.users.owner.active,
          detail: plural(summary.users.owner.inactive, "inactivo", "inactivos")
        },
        {
          label: "Administradores activos",
          count: summary.users.admin.active,
          detail: plural(summary.users.admin.inactive, "inactivo", "inactivos")
        },
        {
          label: "Empleados activos",
          count: summary.users.employee.active,
          detail: plural(summary.users.employee.inactive, "dado de baja", "dados de baja")
        }
      ]
    : [];

  return (
    <div className="dashboard-panel">
      <div className="dashboard-panel-header">
        <div className="dashboard-panel-heading">
          <div>
            <h1>Resumen</h1>
            <p className="dashboard-panel-subtitle">
              Cuántas empresas y personas hay en CEN y qué cambió últimamente. Aquí solo hay
              conteos: la nómina de cada empresa la ven sus dueños.
            </p>
          </div>
        </div>
        <div className="dashboard-panel-actions">
          <button className="btn btn-line" onClick={() => navigate("/superadmin/duenos")}>
            <UsersThree weight="bold" />
            Dueños
          </button>
          <button className="btn btn-line" onClick={() => navigate("/superadmin/empresas")}>
            <Buildings weight="bold" />
            Empresas
          </button>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {failed && (
          <ErrorMessage
            key="error"
            message="No se pudo cargar el resumen. Recarga la página o entra a Dueños o Empresas."
          />
        )}
      </AnimatePresence>

      {summary === null && !failed && (
        <>
          <p className="visually-hidden" role="status">
            Cargando el resumen
          </p>
          <div className="stat-row" aria-hidden="true">
            {[0, 1, 2, 3].map((index) => (
              <div className="stat-card" key={index}>
                <Skeleton width="36px" height={36} />
                <div className="skeleton-stack" style={{ flex: 1 }}>
                  <Skeleton width="70%" height={11} />
                  <Skeleton width="50%" height={16} />
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {isEmpty && (
        <div className="empty-state">
          <span className="empty-state-icon" aria-hidden="true">
            <Buildings weight="bold" />
          </span>
          <p className="empty-state-title">Todavía no hay empresas en CEN</p>
          <p>
            Da de alta al primer dueño y después su empresa. Cada empresa nace con al menos un
            dueño activo.
          </p>
          <button className="btn btn-line" onClick={() => navigate("/superadmin/duenos")}>
            <UserCirclePlus weight="bold" />
            Dar de alta al primer dueño
          </button>
        </div>
      )}

      {summary && !isEmpty && (
        <div className="owner-body">
          <motion.div
            className="stat-row"
            variants={stackTravel}
            initial="initial"
            animate="animate"
          >
            {cards.map((card) => (
              <motion.div key={card.label} className="stat-card" variants={blockTravel}>
                <div>
                  <p className="stat-card-label">{card.label}</p>
                  <p className="stat-card-value">{formatInteger(card.count)}</p>
                  <p className="kpi-detail">{card.detail}</p>
                </div>
              </motion.div>
            ))}
          </motion.div>

          <section className="owner-card" aria-labelledby="titulo-sin-dueno">
            <h2 id="titulo-sin-dueno">Empresas sin dueño activo</h2>
            {summary.orphaned.total === 0 ? (
              <p className="owner-card-note">
                Todas las empresas tienen al menos un dueño activo.
              </p>
            ) : (
              <>
                <p className="owner-card-note">
                  Ningún dueño puede verlas ni administrarlas hasta que tengan uno activo.
                </p>
                <div className="table-wrap">
                  <table className="data-table owner-compact-table">
                    <caption className="visually-hidden">Empresas sin dueño activo</caption>
                    <thead>
                      <tr>
                        <th scope="col">Empresa</th>
                        <th scope="col">Estado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {summary.orphaned.companies.map((company) => (
                        <tr key={company.id}>
                          <td className="name">{company.legal_name}</td>
                          <td>{company.is_active ? "Activa" : "Inactiva"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {hiddenOrphans > 0 && (
                  <p className="owner-card-note">
                    Y {plural(hiddenOrphans, "empresa más", "empresas más")}.
                  </p>
                )}
                <button
                  className="btn btn-line"
                  style={{ marginTop: "var(--s-4)" }}
                  onClick={() => navigate("/superadmin/empresas")}
                >
                  <Buildings weight="bold" />
                  Ir a empresas
                </button>
              </>
            )}
          </section>

          <section className="owner-card" aria-labelledby="titulo-altas">
            <h2 id="titulo-altas">Altas por mes</h2>
            <p className="owner-card-note">Empresas y dueños nuevos en los últimos 12 meses.</p>
            <StackedColumnChart
              label="Empresas y dueños nuevos por mes"
              series={SIGNUP_SERIES}
              formatValue={formatInteger}
              columns={summary.signups.map((month) => ({
                key: month.month,
                label: formatMonthShort(month.month),
                values: { companies: month.companies, owners: month.owners }
              }))}
            />
            <ChartTable
              caption="Empresas y dueños nuevos por mes"
              columns={[
                { label: "Mes" },
                { label: "Empresas", numeric: true },
                { label: "Dueños", numeric: true }
              ]}
              rows={summary.signups.map((month) => ({
                key: month.month,
                cells: [
                  formatMonth(month.month),
                  formatInteger(month.companies),
                  formatInteger(month.owners)
                ]
              }))}
            />
          </section>

          <section className="owner-card" aria-labelledby="titulo-actividad">
            <h2 id="titulo-actividad">Actividad reciente</h2>
            {summary.activity.length === 0 ? (
              <p className="owner-card-note">Todavía no hay movimientos registrados.</p>
            ) : (
              <>
                <p className="owner-card-note">
                  Los últimos movimientos sobre dueños y empresas, de quien los hizo.
                </p>
                <div className="table-wrap">
                  <table className="data-table owner-compact-table">
                    <caption className="visually-hidden">Últimos movimientos de la plataforma</caption>
                    <thead>
                      <tr>
                        <th scope="col">Movimiento</th>
                        <th scope="col">Quién y cuándo</th>
                      </tr>
                    </thead>
                    <tbody>
                      {summary.activity.map((entry) => (
                        <tr key={entry.id}>
                          <td className="name">
                            {entry.target_name ?? "Registro borrado"}
                            <p className="kpi-detail">{actionLabel(entry.action)}</p>
                          </td>
                          <td>
                            {entry.actor_name}
                            <p className="kpi-detail">{formatDateShort(entry.created_at)}</p>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
