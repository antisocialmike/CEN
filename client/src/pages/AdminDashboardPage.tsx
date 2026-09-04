import { useNavigate } from "react-router-dom";
import { logout } from "../services/authService";

export default function AdminDashboardPage() {
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="placeholder-shell">
      <h1>Panel de administrador</h1>
      <p>El cálculo de nómina se agrega en la siguiente etapa.</p>
      <button className="logout-link" onClick={handleLogout}>
        Cerrar sesión
      </button>
    </div>
  );
}
