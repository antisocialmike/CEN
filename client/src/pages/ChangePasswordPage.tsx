import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence } from "motion/react";
import { Lock, ShieldCheck } from "@phosphor-icons/react";
import FormField from "../components/FormField";
import ErrorMessage from "../components/ErrorMessage";
import SubmitButton from "../components/SubmitButton";
import { LogoMark } from "../components/icons";
import ThemeToggle from "../components/ThemeToggle";
import { changePassword } from "../services/authService";
import { dashboardPathForRole, mustChangePassword } from "../services/authSession";
import { getStatusCode } from "../services/apiError";

export default function ChangePasswordPage() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pendingConfirmation, setPendingConfirmation] = useState(false);
  const navigate = useNavigate();

  const isForced = mustChangePassword();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);

    if (newPassword !== confirmation) {
      setErrorMessage("La confirmación no coincide con la contraseña nueva.");
      return;
    }

    setPendingConfirmation(true);
  }

  async function confirmPasswordChange() {
    setIsSubmitting(true);

    try {
      await changePassword(currentPassword, newPassword);
      navigate(dashboardPathForRole(), { replace: true });
    } catch (error) {
      if (getStatusCode(error) === 400) {
        setErrorMessage("La contraseña actual no es correcta, o la nueva es igual a la anterior.");
      } else if (getStatusCode(error) === 422) {
        setErrorMessage("La contraseña nueva debe tener entre 8 y 72 caracteres.");
      } else {
        setErrorMessage("No se pudo cambiar la contraseña. Inténtalo de nuevo.");
      }
      setIsSubmitting(false);
      setPendingConfirmation(false);
    }
  }

  return (
    <div className="auth-page is-single">
      <main className="auth-panel">
        <span className="brand-logo auth-mobile-brand">
          <LogoMark />
          <div className="brand-logo-text">
            <span>CEN Payroll</span>
            <small>Sistema de nómina</small>
          </div>
        </span>

        <div className="auth-card">
          <span className="auth-card-badge" aria-hidden="true">
            <ShieldCheck weight="bold" />
          </span>

          <h1 className="auth-card-title">
            {isForced ? "Elige tu contraseña" : "Cambiar contraseña"}
          </h1>
          <p className="auth-card-subtitle">
            {isForced
              ? "Entraste con una contraseña temporal. Define una propia para continuar."
              : "Necesitas tu contraseña actual para poder cambiarla."}
          </p>

          <AnimatePresence mode="wait">
            {errorMessage && <ErrorMessage key="error" message={errorMessage} />}
          </AnimatePresence>

          <form onSubmit={handleSubmit}>
            <FormField
              id="currentPassword"
              label={isForced ? "Contraseña temporal" : "Contraseña actual"}
              type="password"
              value={currentPassword}
              onChange={setCurrentPassword}
              autoComplete="current-password"
              icon={<Lock weight="bold" />}
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
              hint="Entre 8 y 72 caracteres. No la compartas con nadie."
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
            {pendingConfirmation && (
              <div className="password-warning" role="alert">
                <p className="password-warning-title">
                  {isForced ? "Establecer contraseña" : "Cambiar contraseña"}
                </p>
                <p className="password-warning-note">
                  {isForced
                    ? "Después de esto, deberás usar tu nueva contraseña para entrar la próxima vez."
                    : "Tu contraseña se cambió. Usa la nueva para entrar la próxima vez."}
                </p>
                <div className="password-warning-actions">
                  <button
                    type="button"
                    className="btn btn-line"
                    onClick={() => setPendingConfirmation(false)}
                    disabled={isSubmitting}
                  >
                    Cancelar
                  </button>
                  <button
                    type="button"
                    className="btn btn-rosa"
                    onClick={confirmPasswordChange}
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? "Guardando…" : "Confirmar"}
                  </button>
                </div>
              </div>
            )}

            {!pendingConfirmation && (
              <SubmitButton
                label="Guardar contraseña"
                loadingLabel="Guardando…"
                isLoading={isSubmitting}
              />
            )}
          </form>
        </div>

        <ThemeToggle />
      </main>
    </div>
  );
}
