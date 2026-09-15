import { Suspense, lazy } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AnimatePresence } from "motion/react";
import ProtectedRoute from "./components/ProtectedRoute";
import AppLoader from "./components/AppLoader";
import PageTransition from "./components/PageTransition";
import RutaDePanel from "./components/RutaDePanel";
import { claveDeTransicion } from "./routes/claveDeTransicion";
import LoginPage from "./pages/LoginPage";
import ChangePasswordPage from "./pages/ChangePasswordPage";

const LandingPage = lazy(() => import("./pages/LandingPage"));
const SignupPage = lazy(() => import("./pages/SignupPage"));
const AdminDashboardPage = lazy(() => import("./pages/AdminDashboardPage"));
const EmployeeDashboardPage = lazy(() => import("./pages/EmployeeDashboardPage"));
const PasswordRecoveryPage = lazy(() => import("./pages/PasswordRecoveryPage"));
const PasswordResetVerifyPage = lazy(() => import("./pages/PasswordResetVerifyPage"));
const EmployeesPage = lazy(() => import("./pages/EmployeesPage"));

export default function App() {
  const location = useLocation();

  return (
    <Suspense fallback={<AppLoader />}>
      <AnimatePresence mode="wait" initial={false}>
        <PageTransition key={claveDeTransicion(location.pathname)}>
          <Routes location={location}>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/password-recovery" element={<PasswordRecoveryPage />} />
            <Route path="/password-reset-verify" element={<PasswordResetVerifyPage />} />

            <Route element={<ProtectedRoute />}>
              <Route
                path="/cambiar-contrasena"
                element={<ChangePasswordPage />}
              />
            </Route>

            <Route element={<ProtectedRoute allowedRole="admin" />}>
              <Route element={<RutaDePanel />}>
                <Route path="/admin" element={<AdminDashboardPage />} />
                <Route path="/admin/empleados" element={<EmployeesPage />} />
              </Route>
              <Route path="/admin/nuevo-empleado" element={<SignupPage />} />
            </Route>

            <Route element={<ProtectedRoute allowedRole="employee" />}>
              <Route element={<RutaDePanel />}>
                <Route path="/empleado" element={<EmployeeDashboardPage />} />
              </Route>
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </PageTransition>
      </AnimatePresence>
    </Suspense>
  );
}
