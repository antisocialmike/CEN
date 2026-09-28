import { FormEvent, useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { AnimatePresence } from "motion/react";
import { EnvelopeSimple, Lock, ArrowLeft } from "@phosphor-icons/react";
import FormField from "../components/FormField";
import ErrorMessage from "../components/ErrorMessage";
import SubmitButton from "../components/SubmitButton";
import { LogoMark } from "../components/icons";
import ThemeToggle from "../components/ThemeToggle";
import httpClient from "../services/httpClient";
import { getErrorDetail, getStatusCode } from "../services/apiError";

function emailFromState(state: unknown): string {
  if (typeof state === "object" && state !== null && "email" in state) {
    const { email } = state as { email: unknown };
    return typeof email === "string" ? email : "";
  }
  return "";
}

export default function PasswordResetVerifyPage() {
  const location = useLocation();
  const requestedEmail = emailFromState(location.state);
  const [email, setEmail] = useState(requestedEmail);
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);

    if (newPassword !== confirmation) {
      setErrorMessage("La confirmación no coincide con la contraseña nueva.");
      return;
    }

    setIsSubmitting(true);

    try {
      await httpClient.post("/auth/password-reset/verify", {
        email,
        code,
        new_password: newPassword,
      });
      navigate("/login", { replace: true });
    } catch (error) {
      setErrorMessage(
        getStatusCode(error) === 429
          ? getErrorDetail(error) ?? "Demasiados intentos. Inténtalo más tarde."
          : "Código inválido, expirado o ya utilizado."
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
          <h1 className="auth-card-title">Verificar código</h1>
          <p className="auth-card-subtitle">
            {requestedEmail
              ? "Si hay una cuenta con ese correo, te enviamos un código de 6 dígitos. Escríbelo junto con tu nueva contraseña."
              : "Ingresa tu correo, el código de verificación y tu nueva contraseña."}
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
            <FormField
              id="code"
              label="Código de verificación"
              type="text"
              value={code}
              onChange={setCode}
              placeholder="123456"
              inputMode="numeric"
              maxLength={6}
              required
            />
            <FormField
              id="newPassword"
              label="Contraseña nueva"
              type="password"
              value={newPassword}
              onChange={setNewPassword}
              autoComplete="new-password"
              placeholder="Mínimo 8 caracteres"
              icon={<Lock weight="bold" />}
              hint="Entre 8 y 72 caracteres."
              required
            />
            <FormField
              id="confirmation"
              label="Repite la contraseña nueva"
              type="password"
              value={confirmation}
              onChange={setConfirmation}
              autoComplete="new-password"
              icon={<Lock weight="bold" />}
              required
            />
            <SubmitButton
              label="Cambiar contraseña"
              loadingLabel="Cambiando…"
              isLoading={isSubmitting}
            />
          </form>

          <p className="auth-card-note">
            ¿No te llegó?{" "}
            <Link className="text-button" to="/password-recovery">
              Pide otro código
            </Link>
          </p>
        </div>

        <ThemeToggle />
      </main>
    </div>
  );
}
