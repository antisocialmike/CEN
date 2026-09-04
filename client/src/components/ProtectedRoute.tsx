import { Navigate, Outlet } from "react-router-dom";
import { getRole, isAuthenticated, UserRole } from "../services/authSession";

interface ProtectedRouteProps {
  allowedRole: UserRole;
}

export default function ProtectedRoute({ allowedRole }: ProtectedRouteProps) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  if (getRole() !== allowedRole) {
    const ownRoute = getRole() === "admin" ? "/admin" : "/empleado";
    return <Navigate to={ownRoute} replace />;
  }

  return <Outlet />;
}
