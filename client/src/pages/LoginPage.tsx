import { FormEvent, MouseEvent, startTransition, useId, useState } from "react";
import { Navigate, Link as RouterLink, useNavigate, useSearchParams } from "react-router-dom";
import { AnimatePresence } from "motion/react";
import { EnvelopeSimple, Lock } from "@phosphor-icons/react";
import FormField from "../components/FormField";
import ErrorMessage from "../components/ErrorMessage";
import SubmitButton from "../components/SubmitButton";
import { LogoMark } from "../components/icons";
import ThemeToggle from "../components/ThemeToggle";
import { useTunel } from "../motion/tunel";
import { getErrorDetail, getStatusCode } from "../services/apiError";
import { login } from "../services/authService";
import { dashboardPathForRole, isAuthenticated } from "../services/authSession";
import NetoDelPeriodo, { type Partida } from "../components/landing/NetoDelPeriodo";
import { desglosar } from "../components/landing/calculoNomina";
import "../styles/skin-acceso.css";

const MUESTRA = desglosar(22000, "mensual");

const PARTIDAS_MUESTRA: Partida[] = [
  { concepto: "Salario bruto", importe: MUESTRA.bruto, tipo: "percepcion" },
  { concepto: "ISR retenido", importe: MUESTRA.isr, tipo: "deduccion" },
  { concepto: "IMSS retenido", importe: MUESTRA.imss, tipo: "deduccion" }
];

// Solo un 401 significa credenciales malas; lo demas no es culpa de quien escribe.
function mensajeDeError(error: unknown): string {
  const status = getStatusCode(error);
  if (status === 401) {
    return "Correo o contraseña incorrectos. Revísalos e inténtalo de nuevo.";
  }
  if (status === 403 || status === 429) {
    return getErrorDetail(error) ?? "No puedes entrar con esta cuenta por ahora.";
  }
  if (status === 503) {
    return "El sistema no puede acceder a sus datos en este momento. Inténtalo en unos minutos.";
  }
  if (status === undefined) {
    return "No se pudo conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.";
  }
  return "No se pudo iniciar sesión. Inténtalo de nuevo.";
}

export default function LoginPage() {
  const idMuestra = useId();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();
  const pasarPorTunel = useTunel();
  const [searchParams] = useSearchParams();
  // Se toma al montar: el login recien hecho guarda la sesion antes de su tunel y no debe cortarlo.
  const [yaTeniaSesion] = useState(isAuthenticated);

  const sessionExpired = searchParams.get("sesion") === "expirada";

  // Sigue siendo un enlace (ctrl+clic abre pestaña); solo el clic normal pasa por el tunel.
  function volverALanding(event: MouseEvent<HTMLAnchorElement>) {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    // El logo de la marca es el mismo que cruza el tunel: lo continua en vez de aparecer otro.
    pasarPorTunel(() => startTransition(() => navigate("/")), {
      origen: event.currentTarget.querySelector("svg"),
      compartido: true
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    // Se toma antes del await: el logo del tunel sale del boton que se presiono.
    const boton = (event.nativeEvent as SubmitEvent).submitter;
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const role = await login(email, password);
      pasarPorTunel(
        () => {
          startTransition(() => {
            navigate(dashboardPathForRole(role), { replace: true });
          });
        },
        { origen: boton }
      );
    } catch (error) {
      setErrorMessage(mensajeDeError(error));
      setIsSubmitting(false);
    }
  }

  // Con sesion no hay nada que pedir: al panel. Si toca cambiar la contrasena, ProtectedRoute lo desvia.
  if (yaTeniaSesion) {
    return <Navigate to={dashboardPathForRole()} replace />;
  }

  return (
    <div className="auth-page">
      <main className="auth-panel">
        <RouterLink className="brand-logo auth-mobile-brand" to="/" onClick={volverALanding}>
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

      <aside className="auth-side rv-escaparate" aria-labelledby={idMuestra}>
        <NetoDelPeriodo
          neto={MUESTRA.neto}
          empleado="Ana Gutiérrez"
          periodo="Julio 2026"
          folio="128"
          partidas={PARTIDAS_MUESTRA}
        />

        <p className="rv-escaparate-pie" id={idMuestra}>
          <b>Ejemplo con datos de muestra.</b> Al entrar verás tus recibos reales, cada uno
          con su folio y su periodo. Las cifras salen de las tablas vigentes, no de un
          porcentaje fijo.
        </p>
      </aside>
    </div>
  );
}
