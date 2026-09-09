import { useEffect, useState } from "react";
import DashboardTopbar from "../components/DashboardTopbar";
import ErrorMessage from "../components/ErrorMessage";
import ReceiptCard from "../components/ReceiptCard";
import Skeleton from "../components/Skeleton";
import { CalendarBlank, Receipt, Wallet } from "@phosphor-icons/react";
import { getMyReceipts, PayrollReceipt } from "../services/payrollService";
import { formatCurrency, formatMonth } from "../services/format";

function byNewestFirst(receipts: PayrollReceipt[]): PayrollReceipt[] {
  return [...receipts].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
}

export default function EmployeeDashboardPage() {
  const [receipts, setReceipts] = useState<PayrollReceipt[] | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    getMyReceipts()
      .then((data) => isMounted && setReceipts(byNewestFirst(data)))
      .catch(() => {
        if (isMounted) {
          setErrorMessage(
            "No pudimos cargar tus recibos. Vuelve a intentarlo en unos minutos."
          );
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const latest = receipts && receipts.length > 0 ? receipts[0] : null;
  const totalWithheld = receipts
    ? receipts.reduce((sum, r) => sum + r.isr_deduction + r.imss_deduction, 0)
    : 0;

  return (
    <div className="dashboard-shell">
      <a className="skip-link" href="#contenido">
        Ir al contenido
      </a>
      <DashboardTopbar context="Portal del empleado" />

      <main className="dashboard-content" id="contenido">
        <div className="dashboard-panel">
          <div className="dashboard-panel-header">
            <div className="dashboard-panel-heading">
              <span className="panel-icon-badge" aria-hidden="true">
                <Receipt weight="bold" />
              </span>
              <div>
                <h1>Mis recibos de nómina</h1>
                <p className="dashboard-panel-subtitle">
                  Cada recibo muestra tu salario bruto, lo que se retuvo por ISR e IMSS y el neto
                  que recibiste.
                </p>
              </div>
            </div>
          </div>

          {errorMessage && <ErrorMessage message={errorMessage} />}

          {receipts === null && !errorMessage && (
            <>
              <p className="visually-hidden" role="status">
                Cargando tus recibos
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
              <div className="receipt-list" aria-hidden="true">
                {[0, 1].map((index) => (
                  <div className="skeleton-card skeleton-stack" key={index}>
                    <Skeleton width="55%" height={18} />
                    <Skeleton height={14} />
                    <Skeleton height={14} />
                    <Skeleton height={14} />
                  </div>
                ))}
              </div>
            </>
          )}

          {receipts && latest && (
            <div className="stat-row">
              <div className="stat-card">
                <span className="stat-card-icon" aria-hidden="true">
                  <Wallet weight="bold" />
                </span>
                <div>
                  <p className="stat-card-label">Último neto recibido</p>
                  <p className="stat-card-value">{formatCurrency(latest.net_salary)}</p>
                </div>
              </div>
              <div className="stat-card">
                <span className="stat-card-icon" aria-hidden="true">
                  <CalendarBlank weight="bold" />
                </span>
                <div>
                  <p className="stat-card-label">Último periodo</p>
                  <p className="stat-card-value is-text">{formatMonth(latest.period_start)}</p>
                </div>
              </div>
              <div className="stat-card">
                <span className="stat-card-icon" aria-hidden="true">
                  <Receipt weight="bold" />
                </span>
                <div>
                  <p className="stat-card-label">
                    Retenido en {receipts.length}{" "}
                    {receipts.length === 1 ? "recibo" : "recibos"}
                  </p>
                  <p className="stat-card-value">{formatCurrency(totalWithheld)}</p>
                </div>
              </div>
            </div>
          )}

          {receipts !== null && receipts.length === 0 && (
            <div className="empty-state">
              <span className="empty-state-icon" aria-hidden="true">
                <Receipt weight="bold" />
              </span>
              <p className="empty-state-title">Todavía no tienes recibos</p>
              <p>
                En cuanto tu administrador calcule tu nómina, el recibo aparecerá aquí con el
                desglose completo. No tienes que hacer nada.
              </p>
            </div>
          )}

          {receipts !== null && receipts.length > 0 && (
            <>
              <div className="section-title-row">
                <h2 className="section-title">Historial</h2>
                <p className="section-note">Del más reciente al más antiguo</p>
              </div>
              <div className="receipt-list">
                {receipts.map((receipt) => (
                  <ReceiptCard key={receipt.id} receipt={receipt} />
                ))}
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
