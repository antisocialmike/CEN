import { useNavigate } from "react-router-dom";
import { logout } from "../services/authService";

export default function EmployeeDashboardPage() {
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="placeholder-shell">
      <h1>Mi recibo de nómina</h1>
      <p>La consulta de tu recibo se agrega en la siguiente etapa.</p>
      <button className="logout-link" onClick={handleLogout}>
        Cerrar sesión
      </button>
    </div>
  );
}
