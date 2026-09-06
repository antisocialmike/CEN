import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "motion/react";
import PageTransition from "../components/PageTransition";
import ErrorMessage from "../components/ErrorMessage";
import ReceiptCard from "../components/ReceiptCard";
import { LogoMark, LogoutIcon, ReceiptIcon, WalletIcon } from "../components/icons";
import { logout } from "../services/authService";
import { getMyReceipts, PayrollReceipt } from "../services/payrollService";

function formatCurrency(value: number): string {
  return value.toLocaleString("es-MX", {
    style: "currency",
    currency: "MXN",
    minimumFractionDigits: 2
  });
}

export default function EmployeeDashboardPage() {
  const [receipts, setReceipts] = useState<PayrollReceipt[] | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;

    getMyReceipts()
      .then((data) => {
        if (isMounted) {
          setReceipts(data);
        }
      })
      .catch(() => {
        if (isMounted) {
          setErrorMessage("No se pudieron cargar tus recibos, intenta de nuevo más tarde");
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <PageTransition>
      <div className="dashboard-shell">
        <div className="dashboard-topbar">
          <div className="brand-logo sm">
            <LogoMark />
            <div className="brand-logo-text">
              <span>CEN Payroll</span>
              <small>Portal del empleado</small>
            </div>
          </div>
          <div className="dashboard-topbar-right">
            <span className="user-chip">
              <span className="user-chip-avatar">E</span>
              <span className="user-chip-role">Empleado</span>
            </span>
            <button className="logout-link" onClick={handleLogout}>
              <LogoutIcon />
              Cerrar sesión
            </button>
          </div>
        </div>

        <motion.div
          className="dashboard-content"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        >
          <div className="dashboard-panel">
            <div className="dashboard-panel-header">
              <div className="dashboard-panel-heading">
                <span className="panel-icon-badge">
                  <ReceiptIcon />
                </span>
                <div>
                  <p className="dashboard-panel-eyebrow">Historial</p>
                  <h1>Mis recibos de nómina</h1>
                </div>
              </div>
            </div>

            {receipts !== null && receipts.length > 0 && (
              <div className="stat-row">
                <div className="stat-card">
                  <span className="stat-card-icon">
                    <ReceiptIcon />
                  </span>
                  <div>
                    <p className="stat-card-label">Recibos generados</p>
                    <p className="stat-card-value">{receipts.length}</p>
                  </div>
                </div>
                <div className="stat-card">
                  <span className="stat-card-icon">
                    <WalletIcon />
                  </span>
                  <div>
                    <p className="stat-card-label">Último neto recibido</p>
                    <p className="stat-card-value">
                      {formatCurrency(
                        receipts.reduce((latest, receipt) =>
                          new Date(receipt.created_at) > new Date(latest.created_at) ? receipt : latest
                        ).net_salary
                      )}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {errorMessage && <ErrorMessage message={errorMessage} />}

            {receipts === null && !errorMessage && (
              <p className="loading-text">Cargando tus recibos...</p>
            )}

            {receipts !== null && receipts.length === 0 && (
              <div className="empty-state">
                <span className="empty-state-icon">
                  <ReceiptIcon />
                </span>
                <p>Todavía no tienes recibos generados. Aparecerán aquí en cuanto tu nómina sea calculada.</p>
              </div>
            )}

            {receipts !== null && receipts.length > 0 && (
              <div className="receipt-list">
                {receipts.map((receipt, index) => (
                  <ReceiptCard key={receipt.id} receipt={receipt} index={index} />
                ))}
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </PageTransition>
  );
}
