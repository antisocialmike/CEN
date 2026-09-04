import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "motion/react";
import PageTransition from "../components/PageTransition";
import ErrorMessage from "../components/ErrorMessage";
import ReceiptCard from "../components/ReceiptCard";
import { logout } from "../services/authService";
import { getMyReceipts, PayrollReceipt } from "../services/payrollService";

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
          <span className="dashboard-topbar-brand">CEN Payroll</span>
          <button className="logout-link" onClick={handleLogout}>
            Cerrar sesión
          </button>
        </div>

        <motion.div
          className="dashboard-content"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        >
          <div className="dashboard-panel">
            <h1>Mis recibos de nómina</h1>

            {errorMessage && <ErrorMessage message={errorMessage} />}

            {receipts === null && !errorMessage && (
              <p className="loading-text">Cargando tus recibos...</p>
            )}

            {receipts !== null && receipts.length === 0 && (
              <p className="loading-text">Todavía no tienes recibos generados.</p>
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
