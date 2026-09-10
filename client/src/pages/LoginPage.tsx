import { FormEvent, useState } from "react";
import { Link as RouterLink, useNavigate, useSearchParams } from "react-router-dom";
import { AnimatePresence } from "motion/react";
import { EnvelopeSimple, Lock } from "@phosphor-icons/react";
import FormField from "../components/FormField";
import ErrorMessage from "../components/ErrorMessage";
import SubmitButton from "../components/SubmitButton";
import { LogoMark } from "../components/icons";
import ThemeToggle from "../components/ThemeToggle";
import { login } from "../services/authService";


export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const sessionExpired = searchParams.get("sesion") === "expirada";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const role = await login(email, password);
      navigate(role === "admin" ? "/admin" : "/empleado", { replace: true });
    } catch {
      setErrorMessage("Correo o contraseña incorrectos. Revísalos e inténtalo de nuevo.");
      setIsSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <aside className="auth-side">
        <RouterLink className="brand-logo on-color" to="/">
          <LogoMark />
          <div className="brand-logo-text">
            <span>CEN Payroll</span>
            <small>Sistema de nómina</small>
          </div>
        </RouterLink>

        <div>
          <p className="auth-side-title">Nómina que cuadra.</p>
          <p className="auth-side-note">
            El ISR y el IMSS calculados conforme a la ley, y un recibo guardado por cada periodo.
          </p>
        </div>
      </aside>

      <main className="auth-panel">
        <RouterLink className="brand-logo auth-mobile-brand" to="/">
          <LogoMark />
          <div className="brand-logo-text">
            <span>CEN Payroll</span>
            <small>Sistema de nómina</small>
          </div>
        </RouterLink>

        <div className="auth-card">
          <h1 className="auth-card-title">Inicia sesión</h1>
          <p className="auth-card-subtitle">Entra con la cuenta que te dio tu administrador.</p>

          <AnimatePresence mode="wait">
            {sessionExpired && !errorMessage && (
              <ErrorMessage
                key="expirada"
                message="Tu sesión expiró por inactividad. Inicia sesión de nuevo para continuar."
              />
            )}
            {errorMessage && <ErrorMessage key="error" message={errorMessage} />}
          </AnimatePresence>

          <form onSubmit={handleSubmit}>
            <FormField
              id="email"
              label="Correo"
              type="email"
              value={email}
              onChange={setEmail}
              autoComplete="username"
              inputMode="email"
              placeholder="nombre@empresa.mx"
              icon={<EnvelopeSimple weight="bold" />}
              required
            />
            <FormField
              id="password"
              label="Contraseña"
              type="password"
              value={password}
              onChange={setPassword}
              autoComplete="current-password"
              placeholder="Tu contraseña"
              icon={<Lock weight="bold" />}
              required
            />
            <SubmitButton label="Ingresar" loadingLabel="Ingresando…" isLoading={isSubmitting} />
          </form>
        </div>

        <ThemeToggle />

        <div className="auth-panel-links">
          <RouterLink to="/password-recovery" className="text-button">
            ¿Olvidaste tu contraseña?
          </RouterLink>
          <p className="auth-panel-foot">
            ¿No tienes cuenta? Tu administrador de nómina la crea por ti.
          </p>
        </div>
      </main>
    </div>
  );
}
