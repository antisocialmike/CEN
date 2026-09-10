import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence } from "motion/react";
import { EnvelopeSimple, ArrowLeft } from "@phosphor-icons/react";
import FormField from "../components/FormField";
import ErrorMessage from "../components/ErrorMessage";
import SuccessMessage from "../components/SuccessMessage";
import SubmitButton from "../components/SubmitButton";
import { LogoMark } from "../components/icons";
import ThemeToggle from "../components/ThemeToggle";
import { httpClient } from "../services/httpClient";

export default function PasswordRecoveryPage() {
  const [email, setEmail] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);
    setIsSubmitting(true);

    try {
      await httpClient.post("/auth/password-reset/request", { email });
      setSuccessMessage("Se envió un código a tu correo. Revisa tu bandeja de entrada.");
      setSubmitted(true);
      setEmail("");
    } catch (error) {
      setErrorMessage("No se pudo enviar el correo. Verifica que el correo sea válido.");
    } finally {
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
            {successMessage && <SuccessMessage key="success" message={successMessage} />}
          </AnimatePresence>

          {!submitted ? (
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
          ) : (
            <p className="auth-card-note">
              ¿No recibiste el correo?{" "}
              <button
                type="button"
                className="text-button"
                onClick={() => setSubmitted(false)}
              >
                Intenta de nuevo
              </button>
            </p>
          )}
        </div>

        <ThemeToggle />
      </main>
    </div>
  );
}
