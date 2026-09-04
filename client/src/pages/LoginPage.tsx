import { FormEvent, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import FormField from "../components/FormField";
import ErrorMessage from "../components/ErrorMessage";
import LoadingSpinner from "../components/LoadingSpinner";
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
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="app-shell">
      <div className="auth-card">
        <p className="auth-brand">CEN Payroll</p>
        <p className="auth-subtitle">Inicia sesión con tu cuenta</p>

        {sessionExpired && (
          <ErrorMessage message="Tu sesión expiró, inicia sesión de nuevo" />
        )}
        {errorMessage && <ErrorMessage message={errorMessage} />}

        <form onSubmit={handleSubmit}>
          <FormField
            id="email"
            label="Correo"
            type="email"
            value={email}
            onChange={setEmail}
            autoComplete="username"
            required
          />
          <FormField
            id="password"
            label="Contraseña"
            type="password"
            value={password}
            onChange={setPassword}
            autoComplete="current-password"
            required
          />
          <button className="submit-button" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Ingresando..." : "Ingresar"}
          </button>
          {isSubmitting && <LoadingSpinner label="Validando credenciales..." />}
        </form>
      </div>
    </div>
  );
}
