import { Suspense, lazy } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AnimatePresence } from "motion/react";
import ProtectedRoute from "./components/ProtectedRoute";
import AppLoader from "./components/AppLoader";

const LandingPage = lazy(() => import("./pages/LandingPage"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const SignupPage = lazy(() => import("./pages/SignupPage"));
const AdminDashboardPage = lazy(() => import("./pages/AdminDashboardPage"));
const EmployeeDashboardPage = lazy(() => import("./pages/EmployeeDashboardPage"));
const ChangePasswordPage = lazy(() => import("./pages/ChangePasswordPage"));
const EmployeesPage = lazy(() => import("./pages/EmployeesPage"));

export default function App() {
  const location = useLocation();

  return (
    <Suspense fallback={<AppLoader />}>
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />

          <Route element={<ProtectedRoute />}>
            <Route path="/cambiar-contrasena" element={<ChangePasswordPage />} />
          </Route>

          <Route element={<ProtectedRoute allowedRole="admin" />}>
            <Route path="/admin" element={<AdminDashboardPage />} />
            <Route path="/admin/nuevo-empleado" element={<SignupPage />} />
            <Route path="/admin/empleados" element={<EmployeesPage />} />
          </Route>

          <Route element={<ProtectedRoute allowedRole="employee" />}>
            <Route path="/empleado" element={<EmployeeDashboardPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AnimatePresence>
    </Suspense>
  );
}
