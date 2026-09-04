import { useNavigate } from "react-router-dom";
import { motion } from "motion/react";
import PageTransition from "../components/PageTransition";
import { UsersIcon } from "../components/icons";
import { logout } from "../services/authService";

export default function AdminDashboardPage() {
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
          <h1>Panel de administrador</h1>
          <p>El cálculo de nómina se agrega en la siguiente etapa.</p>
          <div className="dashboard-actions">
            <button
              className="secondary-button"
              onClick={() => navigate("/admin/nuevo-empleado")}
            >
              <UsersIcon />
              Dar de alta empleado
            </button>
          </div>
        </motion.div>
      </div>
    </PageTransition>
  );
}
