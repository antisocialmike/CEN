import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import FormField from "../components/FormField";
import SelectField from "../components/SelectField";
import ErrorMessage from "../components/ErrorMessage";
import SuccessMessage from "../components/SuccessMessage";
import SubmitButton from "../components/SubmitButton";
import PageTransition from "../components/PageTransition";
import { UsersIcon, MailIcon, LockIcon } from "../components/icons";
import { createEmployee } from "../services/employeeService";
import { UserRole } from "../services/authSession";
import { getStatusCode } from "../services/apiError";

const emptyForm = {
  name: "",
  email: "",
  role: "employee" as UserRole,
  baseSalary: "",
  password: ""
};

export default function SignupPage() {
  const [form, setForm] = useState(emptyForm);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  function updateField<K extends keyof typeof emptyForm>(key: K, value: (typeof emptyForm)[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);
    setIsSubmitting(true);

    try {
      const created = await createEmployee({
        name: form.name,
        email: form.email,
        role: form.role,
        baseSalary: Number(form.baseSalary),
        password: form.password
      });
      setSuccessMessage(`Empleado ${created.name} dado de alta correctamente`);
      setForm(emptyForm);
    } catch (error) {
      if (getStatusCode(error) === 409) {
        setErrorMessage("El correo ya está registrado");
      } else {
        setErrorMessage("No se pudo dar de alta al empleado, intenta de nuevo");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <PageTransition>
      <div className="signup-page">
        <motion.div
          className="auth-card"
          initial={{ opacity: 0, y: 20, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        >
          <button className="signup-back-link" onClick={() => navigate("/admin")}>
            ← Volver al panel
          </button>
          <p className="auth-brand">Dar de alta empleado</p>
          <p className="auth-subtitle">Crea una cuenta nueva para tu equipo</p>

          <AnimatePresence mode="wait">
            {errorMessage && <ErrorMessage key="error" message={errorMessage} />}
            {successMessage && <SuccessMessage key="success" message={successMessage} />}
          </AnimatePresence>

          <form onSubmit={handleSubmit}>
            <FormField
              id="name"
              label="Nombre completo"
              type="text"
              value={form.name}
              onChange={(value) => updateField("name", value)}
              icon={<UsersIcon />}
              required
            />
            <FormField
              id="email"
              label="Correo"
              type="email"
              value={form.email}
              onChange={(value) => updateField("email", value)}
              autoComplete="off"
              icon={<MailIcon />}
              required
            />
            <SelectField
              id="role"
              label="Rol"
              value={form.role}
              onChange={(value) => updateField("role", value as UserRole)}
              options={[
                { value: "employee", label: "Empleado" },
                { value: "admin", label: "Administrador" }
              ]}
            />
            <FormField
              id="baseSalary"
              label="Salario base mensual"
              type="number"
              value={form.baseSalary}
              onChange={(value) => updateField("baseSalary", value)}
              min={0}
              step={0.01}
              required
            />
            <FormField
              id="password"
              label="Contraseña temporal"
              type="password"
              value={form.password}
              onChange={(value) => updateField("password", value)}
              autoComplete="new-password"
              icon={<LockIcon />}
              required
            />
            <SubmitButton
              label="Dar de alta"
              loadingLabel="Guardando..."
              isLoading={isSubmitting}
            />
          </form>
        </motion.div>
      </div>
    </PageTransition>
  );
}
