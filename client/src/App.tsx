import { Suspense, lazy, useCallback, useEffect, useState } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AnimatePresence } from "motion/react";
import ProtectedRoute from "./components/ProtectedRoute";
import AppLoader from "./components/AppLoader";
import PageTransition from "./components/PageTransition";
import RutaDePanel from "./components/RutaDePanel";
import { claveDeTransicion } from "./routes/claveDeTransicion";

import LoginPage from "./pages/LoginPage";
import ChangePasswordPage from "./pages/ChangePasswordPage";
import PasswordRecoveryPage from "./pages/PasswordRecoveryPage";
import PasswordResetVerifyPage from "./pages/PasswordResetVerifyPage";
import SignupPage from "./pages/SignupPage";

const LandingPage = lazy(() => import("./pages/LandingPage"));
const AdminDashboardPage = lazy(() => import("./pages/AdminDashboardPage"));
const EmployeeDashboardPage = lazy(() => import("./pages/EmployeeDashboardPage"));
const EmployeesPage = lazy(() => import("./pages/EmployeesPage"));

// Se monta junto al contenido de la Suspense: su efecto solo corre cuando ya resolvio lo perezoso.
function AvisaAlMontar({ alMontar }: { alMontar: () => void }) {
  useEffect(alMontar, [alMontar]);
  return null;
}

export default function App() {
  const location = useLocation();
  // El splash con intro es solo para el arranque en frio de la landing; las demas rutas entran directo.
  const [splash, setSplash] = useState(() => location.pathname === "/");
  const [contenidoListo, setContenidoListo] = useState(false);
  const marcarListo = useCallback(() => setContenidoListo(true), []);
  const cerrarSplash = useCallback(() => setSplash(false), []);

  return (
    <>
      <Suspense fallback={splash ? null : <AppLoader intro={false} />}>
        <AvisaAlMontar alMontar={marcarListo} />
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
      {splash && <AppLoader listo={contenidoListo} alTerminar={cerrarSplash} />}
    </>
  );
}
