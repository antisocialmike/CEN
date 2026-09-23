import { MouseEvent, startTransition } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Key, SignOut } from "@phosphor-icons/react";
import { LogoMark } from "./icons";
import ThemeToggle from "./ThemeToggle";
import { useTunel } from "../motion/tunel";
import { logout } from "../services/authService";
import { getInitials, getName, getRoleLabel } from "../services/authSession";

interface DashboardTopbarProps {
  context: string;
}

export default function DashboardTopbar({ context }: DashboardTopbarProps) {
  const navigate = useNavigate();
  const pasarPorTunel = useTunel();
  const name = getName();
  const roleLabel = getRoleLabel();

  // Sigue siendo un enlace (ctrl+clic abre pestaña); solo el clic normal pasa por el tunel.
  function volverALanding(event: MouseEvent<HTMLAnchorElement>) {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    pasarPorTunel(() => startTransition(() => navigate("/")), {
      origen: event.currentTarget.querySelector("svg"),
      compartido: true
    });
  }

  function handleLogout(event: MouseEvent<HTMLButtonElement>) {
    // La sesion se cierra ya tapada: el panel no llega a pintarse sin usuario.
    pasarPorTunel(
      () => {
        logout();
        navigate("/login", { replace: true });
      },
      { origen: event.currentTarget }
    );
  }

  return (
    <header className="dashboard-topbar">
      <Link className="brand-logo sm" to="/" onClick={volverALanding}>
        <LogoMark />
        <div className="brand-logo-text">
          <span>CEN Payroll</span>
          <small>{context}</small>
        </div>
      </Link>

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
        <button
          className="logout-link"
          onClick={() => navigate("/cambiar-contrasena")}
        >
          <Key weight="bold" />
          <span>Contraseña</span>
        </button>
        <button className="logout-link" onClick={handleLogout}>
          <SignOut weight="bold" />
          <span>Cerrar sesión</span>
        </button>
      </div>
    </header>
  );
}
