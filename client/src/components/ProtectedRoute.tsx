import { Navigate, Outlet, useLocation } from "react-router-dom";
import {
  dashboardPathForRole,
  getRole,
  isAuthenticated,
  mustChangePassword,
  UserRole
} from "../services/authSession";

const CHANGE_PASSWORD_PATH = "/cambiar-contrasena";

interface ProtectedRouteProps {
  allowedRole?: UserRole;
}

export default function ProtectedRoute({ allowedRole }: ProtectedRouteProps) {
  const location = useLocation();

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  const isChangingPassword = location.pathname === CHANGE_PASSWORD_PATH;

  if (mustChangePassword() && !isChangingPassword) {
    return <Navigate to={CHANGE_PASSWORD_PATH} replace />;
  }

  if (!mustChangePassword() && isChangingPassword) {
    return <Outlet />;
  }

  if (allowedRole && getRole() !== allowedRole) {
    return <Navigate to={dashboardPathForRole()} replace />;
  }

  return <Outlet />;
}
