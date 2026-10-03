import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import { UserPlus, UsersThree, Wallet } from "@phosphor-icons/react";
import { blockVariants, stackVariants, useStill } from "../motion/variants";
import ErrorMessage from "../components/ErrorMessage";
import Skeleton from "../components/Skeleton";
import BarList from "../components/charts/BarList";
import { AdminSummary, getAdminSummary } from "../services/adminSummaryService";
import { TIPO_REGIMEN_LABELS } from "../services/employeeService";
import {
  formatCurrency,
  formatDateShort,
  formatInteger,
  formatMonth
} from "../services/format";
import "../styles/skin-dueno.css";

const PERSONAS = "var(--viz-percepcion)";

function plural(count: number, one: string, many: string): string {
  return `${formatInteger(count)} ${count === 1 ? one : many}`;
}

export default function AdminSummaryPage() {
  const stackTravel = useStill(stackVariants);
  const blockTravel = useStill(blockVariants);
  const navigate = useNavigate();
  const [summary, setSummary] = useState<AdminSummary | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let isMounted = true;

    getAdminSummary()
      .then((data) => isMounted && setSummary(data))
      .catch(() => isMounted && setFailed(true));

    return () => {
      isMounted = false;
    };
  }, []);

  const month = summary ? formatMonth(summary.month).toLowerCase() : "";
  const last = summary?.last_month ?? null;
  const isEmpty =
    summary !== null &&
    summary.on_payroll === 0 &&
    last === null &&
    summary.movements.length === 0;
  const hiddenPending = summary ? summary.pending.total - summary.pending.people.length : 0;

  return (
    <div className="dashboard-panel">
      <div className="dashboard-panel-header">
        <div className="dashboard-panel-heading">
          <div>
            <h1>Resumen</h1>
            <p className="dashboard-panel-subtitle">
              Quién falta de calcular este mes, cómo cerró el último mes con recibos y quién entró
              o salió de la empresa.
            </p>
          </div>
        </div>
        <div className="dashboard-panel-actions">
          <button className="btn btn-rosa" onClick={() => navigate("/admin/nomina")}>
            <Wallet weight="bold" />
            Calcular nómina
          </button>
          <button className="btn btn-line" onClick={() => navigate("/admin/usuarios")}>
            <UsersThree weight="bold" />
            Usuarios
          </button>
          <button className="btn btn-line" onClick={() => navigate("/admin/nuevo-usuario")}>
            <UserPlus weight="bold" />
            Dar de alta usuario
          </button>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {failed && (
          <ErrorMessage
            key="error"
            message="No se pudo cargar el resumen. Recarga la página o entra directo a calcular la nómina."
          />
        )}
      </AnimatePresence>

      {summary === null && !failed && (
        <>
          <p className="visually-hidden" role="status">
            Cargando el resumen
          </p>
          <div className="stat-row" aria-hidden="true">
            {[0, 1, 2].map((index) => (
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
            <UsersThree weight="bold" />
          </span>
          <p className="empty-state-title">Todavía no hay nadie en la nómina</p>
          <p>
            Da de alta al primer usuario y podrás calcular su ISR e IMSS y emitir su recibo en el
            mismo paso.
          </p>
          <button className="btn btn-line" onClick={() => navigate("/admin/nuevo-usuario")}>
            <UserPlus weight="bold" />
            Dar de alta al primer usuario
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
            <motion.div className="stat-card" variants={blockTravel}>
              <div>
                <p className="stat-card-label">Sin recibo en {month}</p>
                <p className="stat-card-value">{formatInteger(summary.pending.total)}</p>
                <p className="kpi-detail">
                  de {plural(summary.on_payroll, "persona", "personas")} en la nómina
                </p>
              </div>
            </motion.div>
            <motion.div className="stat-card" variants={blockTravel}>
              <div>
                <p className="stat-card-label">Neto del último mes con recibos</p>
                <p className="stat-card-value is-neto">
                  {last ? formatCurrency(last.net_paid) : "—"}
                </p>
                <p className="kpi-detail">
                  {last
                    ? `${formatMonth(last.month)} · ${plural(last.receipts, "recibo", "recibos")}`
                    : "Aún no hay recibos"}
                </p>
              </div>
            </motion.div>
            <motion.div className="stat-card" variants={blockTravel}>
              <div>
                <p className="stat-card-label">En la nómina</p>
                <p className="stat-card-value">{formatInteger(summary.on_payroll)}</p>
                <p className="kpi-detail">Activos y con salario</p>
              </div>
            </motion.div>
          </motion.div>

          <div className="owner-grid">
            <section className="owner-card" aria-labelledby="titulo-pendientes">
              <h2 id="titulo-pendientes">Pendientes de {month}</h2>
              {summary.pending.total === 0 ? (
                <p className="owner-card-note">
                  {summary.on_payroll === 0
                    ? "No hay nadie activo en la nómina."
                    : `Todos tienen al menos un recibo de ${month}.`}
                </p>
              ) : (
                <>
                  <p className="owner-card-note">
                    Personas en la nómina sin ningún recibo que empiece este mes.
                  </p>
                  <div className="table-wrap">
                    <table className="data-table owner-compact-table">
                      <caption className="visually-hidden">Personas sin recibo en {month}</caption>
                      <thead>
                        <tr>
                          <th scope="col">Persona</th>
                          <th scope="col">Tipo</th>
                        </tr>
                      </thead>
                      <tbody>
                        {summary.pending.people.map((person) => (
                          <tr key={person.id}>
                            <td className="name">{person.name}</td>
                            <td>{person.tipo_regimen === "09" ? "Asimilado" : "Sueldos"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {hiddenPending > 0 && (
                    <p className="owner-card-note">
                      Y {plural(hiddenPending, "persona más", "personas más")}.
                    </p>
                  )}
                  <button
                    className="btn btn-line"
                    style={{ marginTop: "var(--s-4)" }}
                    onClick={() => navigate("/admin/nomina")}
                  >
                    <Wallet weight="bold" />
                    Calcular nómina
                  </button>
                </>
              )}
            </section>

            <section className="owner-card" aria-labelledby="titulo-ultimo-mes">
              <h2 id="titulo-ultimo-mes">
                {last ? `Último mes: ${formatMonth(last.month)}` : "Último mes con recibos"}
              </h2>
              {last === null ? (
                <p className="owner-card-note">Todavía no se ha emitido ningún recibo.</p>
              ) : (
                <>
                  <p className="owner-card-note">
                    {plural(last.receipts, "recibo", "recibos")} de{" "}
                    {plural(last.paid_people, "persona", "personas")}, por el inicio de cada
                    periodo.
                  </p>
                  <div className="table-wrap">
                    <table className="data-table owner-compact-table">
                      <caption className="visually-hidden">
                        Totales de {formatMonth(last.month)}
                      </caption>
                      <tbody>
                        {[
                          { label: "Bruto", amount: last.gross_payroll },
                          { label: "ISR retenido", amount: last.isr_withheld },
                          { label: "IMSS retenido", amount: last.imss_withheld },
                          { label: "Neto pagado", amount: last.net_paid }
                        ].map((row) => (
                          <tr key={row.label}>
                            <th scope="row">{row.label}</th>
                            <td className="num">{formatCurrency(row.amount)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </section>
          </div>

          <div className="owner-grid">
            <section className="owner-card" aria-labelledby="titulo-movimientos">
              <h2 id="titulo-movimientos">Altas y bajas recientes</h2>
              {summary.movements.length === 0 ? (
                <p className="owner-card-note">Sin altas ni bajas registradas.</p>
              ) : (
                <div className="table-wrap">
                  <table className="data-table owner-compact-table">
                    <caption className="visually-hidden">Últimas altas y bajas</caption>
                    <thead>
                      <tr>
                        <th scope="col">Persona</th>
                        <th scope="col">Movimiento</th>
                      </tr>
                    </thead>
                    <tbody>
                      {summary.movements.map((movement) => (
                        <tr key={`${movement.kind}-${movement.id}`}>
                          <td className="name">{movement.name}</td>
                          <td>
                            {movement.kind === "alta" ? "Alta" : "Baja"} ·{" "}
                            {formatDateShort(movement.happened_at)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>

            <section className="owner-card" aria-labelledby="titulo-tipos">
              <h2 id="titulo-tipos">Tipo de nómina</h2>
              <p className="owner-card-note">Personas activas y con salario.</p>
              <BarList
                label="Personas por tipo de nómina"
                color={PERSONAS}
                formatValue={formatInteger}
                items={summary.regimes.map((regime) => ({
                  id: regime.tipo_regimen,
                  label: TIPO_REGIMEN_LABELS[regime.tipo_regimen],
                  value: regime.people
                }))}
              />
            </section>
          </div>
        </div>
      )}
    </div>
  );
}
