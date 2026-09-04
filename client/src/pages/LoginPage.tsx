import { FormEvent, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import FormField from "../components/FormField";
import ErrorMessage from "../components/ErrorMessage";
import SubmitButton from "../components/SubmitButton";
import PageTransition from "../components/PageTransition";
import { MailIcon, LockIcon } from "../components/icons";
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
      setErrorMessage("Correo o contraseña incorrectos");
      setIsSubmitting(false);
    }
  }

  return (
    <PageTransition>
      <div className="auth-page">
        <motion.div
          className="auth-branding"
          initial={{ opacity: 0, x: -24 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        >
          <motion.span
            className="auth-branding-shape one"
            animate={{ scale: [1, 1.08, 1] }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.span
            className="auth-branding-shape two"
            animate={{ scale: [1, 1.12, 1] }}
            transition={{ duration: 7, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
          />
          <p className="auth-branding-title">Nómina clara, segura y a tiempo para tu equipo</p>
          <p className="auth-branding-subtitle">
            Calcula ISR e IMSS conforme a la ley, controla el acceso por rol y entrega recibos
            auditables desde un solo lugar.
          </p>
        </motion.div>

        <div className="auth-form-panel">
          <motion.div
            className="auth-card"
            initial={{ opacity: 0, y: 20, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.45, ease: "easeOut", delay: 0.1 }}
          >
            <p className="auth-brand">CEN Payroll</p>
            <p className="auth-subtitle">Inicia sesión con tu cuenta</p>

            <AnimatePresence mode="wait">
              {sessionExpired && !errorMessage && (
                <ErrorMessage
                  key="expirada"
                  message="Tu sesión expiró, inicia sesión de nuevo"
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
                icon={<MailIcon />}
                required
              />
              <FormField
                id="password"
                label="Contraseña"
                type="password"
                value={password}
                onChange={setPassword}
                autoComplete="current-password"
                icon={<LockIcon />}
                required
              />
              <SubmitButton
                label="Ingresar"
                loadingLabel="Ingresando..."
                isLoading={isSubmitting}
              />
            </form>
          </motion.div>
        </div>
      </div>
    </PageTransition>
  );
}
