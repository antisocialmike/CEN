import { useNavigate } from "react-router-dom";
import { SignOut } from "@phosphor-icons/react";
import { LogoMark } from "./icons";
import ThemeToggle from "./ThemeToggle";
import { logout } from "../services/authService";
import { getInitials, getName, getRoleLabel } from "../services/authSession";

interface DashboardTopbarProps {
  context: string;
}

export default function DashboardTopbar({ context }: DashboardTopbarProps) {
  const navigate = useNavigate();
  const name = getName();
  const roleLabel = getRoleLabel();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <header className="dashboard-topbar">
      <div className="brand-logo sm">
        <LogoMark />
        <div className="brand-logo-text">
          <span>CEN Payroll</span>
          <small>{context}</small>
        </div>
      </div>

      <div className="dashboard-topbar-right">
        <span className="user-chip">
          <span className="user-chip-avatar" aria-hidden="true">
            {getInitials()}
          </span>
          <span className="user-chip-text">
            <span className="user-chip-name">{name || roleLabel}</span>
            {name && <span className="user-chip-role">{roleLabel}</span>}
          </span>
        </span>
        <ThemeToggle />
        <button className="logout-link" onClick={handleLogout}>
          <SignOut weight="bold" />
          <span>Cerrar sesión</span>
        </button>
      </div>
    </header>
  );
}
