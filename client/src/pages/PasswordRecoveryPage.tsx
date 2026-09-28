import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AnimatePresence } from "motion/react";
import { EnvelopeSimple, ArrowLeft } from "@phosphor-icons/react";
import FormField from "../components/FormField";
import ErrorMessage from "../components/ErrorMessage";
import SubmitButton from "../components/SubmitButton";
import { LogoMark } from "../components/icons";
import ThemeToggle from "../components/ThemeToggle";
import httpClient from "../services/httpClient";
import { getErrorDetail, getStatusCode } from "../services/apiError";

export default function PasswordRecoveryPage() {
  const [email, setEmail] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      await httpClient.post("/auth/password-reset/request", { email });
      // El código solo vale para el correo que lo pidió: la verificación lo necesita.
      navigate("/password-reset-verify", { state: { email } });
    } catch (error) {
      setErrorMessage(
        getStatusCode(error) === 429
          ? getErrorDetail(error) ?? "Demasiadas solicitudes. Inténtalo más tarde."
          : "No se pudo enviar el correo. Verifica que el correo sea válido."
      );
      setIsSubmitting(false);
    }
  }

  return (
    <div className="auth-page is-single">
      <main className="auth-panel">
        <Link className="auth-back" to="/login">
          <ArrowLeft weight="bold" />
          Volver
        </Link>

        <span className="brand-logo auth-mobile-brand">
          <LogoMark />
          <div className="brand-logo-text">
            <span>CEN Payroll</span>
            <small>Sistema de nómina</small>
          </div>
        </span>

        <div className="auth-card">
          <h1 className="auth-card-title">Restablecer contraseña</h1>
          <p className="auth-card-subtitle">
            Ingresa tu correo para recibir un código de verificación.
          </p>

          <AnimatePresence mode="wait">
            {errorMessage && <ErrorMessage key="error" message={errorMessage} />}
          </AnimatePresence>

          <form onSubmit={handleSubmit}>
            <FormField
              id="email"
              label="Correo"
              type="email"
              value={email}
              onChange={setEmail}
              autoComplete="email"
              inputMode="email"
              placeholder="tu@empresa.mx"
              icon={<EnvelopeSimple weight="bold" />}
              required
            />
            <SubmitButton
              label="Enviar código"
              loadingLabel="Enviando…"
              isLoading={isSubmitting}
            />
          </form>
        </div>

        <ThemeToggle />
      </main>
    </div>
  );
}
