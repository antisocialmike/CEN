import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence } from "motion/react";
import {
  ArrowLeft,
  CalendarBlank,
  EnvelopeSimple,
  Lock,
  UsersThree
} from "@phosphor-icons/react";
import FormField from "../components/FormField";
import SelectField from "../components/SelectField";
import ErrorMessage from "../components/ErrorMessage";
import SuccessMessage from "../components/SuccessMessage";
import SubmitButton from "../components/SubmitButton";
import {
  createEmployee,
  TIPO_JORNADA_LABELS,
  TIPO_REGIMEN_LABELS,
  TipoJornada,
  TipoRegimen
} from "../services/employeeService";
import { EmployeeRole } from "../services/authSession";
import { getStatusCode } from "../services/apiError";
import { currentDate } from "../services/format";

const emptyForm = {
  name: "",
  email: "",
  role: "employee" as EmployeeRole,
  baseSalary: "",
  password: "",
  tipoRegimen: "02" as TipoRegimen,
  tipoJornada: "01" as TipoJornada,
  hireDate: ""
};

function newForm(): typeof emptyForm {
  return { ...emptyForm, hireDate: currentDate() };
}

export default function SignupPage() {
  const [form, setForm] = useState(newForm);
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
        password: form.password,
        tipoRegimen: form.tipoRegimen,
        tipoJornada: form.tipoJornada,
        hireDate: form.hireDate
      });
      setSuccessMessage(
        `${created.name} ya puede entrar con ${created.email}. Comparte con esa persona su contraseña temporal.`
      );
      setForm(newForm());
    } catch (error) {
      if (getStatusCode(error) === 409) {
        setErrorMessage("Ese correo ya está registrado. Usa otro o busca a la persona en la lista.");
      } else {
        setErrorMessage("No se pudo dar de alta al usuario. Revisa los datos e inténtalo de nuevo.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="signup-page">
      <main className="signup-card">
        <button className="text-button" onClick={() => navigate("/admin")}>
          <ArrowLeft weight="bold" />
          Volver al panel
        </button>

        <div style={{ margin: "20px 0 28px" }}>
          <h1 className="auth-card-title">Dar de alta usuario</h1>
          <p className="auth-card-subtitle" style={{ marginBottom: 0 }}>
            La persona entrará con su correo y la contraseña temporal que definas aquí.
          </p>
        </div>

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
            autoComplete="off"
            placeholder="Ana Sofía Ramírez"
            icon={<UsersThree weight="bold" />}
            required
          />
          <FormField
            id="email"
            label="Correo"
            type="email"
            value={form.email}
            onChange={(value) => updateField("email", value)}
            autoComplete="off"
            inputMode="email"
            placeholder="nombre@empresa.mx"
            icon={<EnvelopeSimple weight="bold" />}
            hint="Será su usuario para iniciar sesión."
            required
          />
          <SelectField
            id="role"
            label="Rol"
            value={form.role}
            onChange={(value) => updateField("role", value as EmployeeRole)}
            options={[
              { value: "employee", label: "Empleado" },
              { value: "admin", label: "Administrador" }
            ]}
            hint={
              form.role === "admin"
                ? "Podrá calcular nómina, dar de alta personas y ver los recibos de todo el equipo."
                : "Solo podrá consultar sus propios recibos."
            }
          />
          <SelectField
            id="tipoRegimen"
            label="Tipo de nómina"
            value={form.tipoRegimen}
            onChange={(value) => updateField("tipoRegimen", value as TipoRegimen)}
            options={Object.entries(TIPO_REGIMEN_LABELS).map(([value, label]) => ({
              value,
              label
            }))}
            hint={
              form.tipoRegimen === "09"
                ? "Sin relación laboral: se le retiene ISR sin subsidio, no cotiza al IMSS y no tiene horas extra, aguinaldo ni prima vacacional."
                : "Trabajador con relación laboral: ISR con subsidio, IMSS y prestaciones de ley."
            }
          />
          {form.tipoRegimen === "02" && (
            <SelectField
              id="tipoJornada"
              label="Jornada"
              value={form.tipoJornada}
              onChange={(value) => updateField("tipoJornada", value as TipoJornada)}
              options={Object.entries(TIPO_JORNADA_LABELS).map(([value, label]) => ({
                value,
                label
              }))}
              hint="Las horas de cada día: con ellas se paga cada hora extra."
            />
          )}
          <FormField
            id="hireDate"
            label="Fecha de ingreso"
            type="date"
            value={form.hireDate}
            onChange={(value) => updateField("hireDate", value)}
            icon={<CalendarBlank weight="bold" />}
            hint="De aquí sale su antigüedad: los días de vacaciones y el salario base de cotización."
            required
          />
          <FormField
            id="baseSalary"
            label="Salario base mensual"
            type="number"
            value={form.baseSalary}
            onChange={(value) => updateField("baseSalary", value)}
            min={0}
            step={0.01}
            inputMode="decimal"
            placeholder="0.00"
            prefix="$"
            hint="Se propondrá como salario bruto al calcular su nómina."
            required
          />
          <FormField
            id="password"
            label="Contraseña temporal"
            type="password"
            value={form.password}
            onChange={(value) => updateField("password", value)}
            autoComplete="new-password"
            placeholder="Mínimo 8 caracteres"
            icon={<Lock weight="bold" />}
            hint="Compártela por un canal seguro; la persona podrá usarla en su primer acceso."
            required
          />
          <SubmitButton label="Dar de alta" loadingLabel="Guardando…" isLoading={isSubmitting} />
        </form>
      </main>
    </div>
  );
}
