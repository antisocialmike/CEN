import { useNavigate } from "react-router-dom";
import { motion } from "motion/react";
import PageTransition from "../components/PageTransition";
import { logout } from "../services/authService";

export default function EmployeeDashboardPage() {
  const navigate = useNavigate();

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
          className="dashboard-body"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        >
          <h1>Mi recibo de nómina</h1>
          <p>La consulta de tu recibo se agrega en la siguiente etapa.</p>
        </motion.div>
      </div>
    </PageTransition>
  );
}
