import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import PageTransition from "../components/PageTransition";
import FormField from "../components/FormField";
import ErrorMessage from "../components/ErrorMessage";
import SubmitButton from "../components/SubmitButton";
import PayrollResultCard from "../components/PayrollResultCard";
import { UsersIcon } from "../components/icons";
import { logout } from "../services/authService";
import { calculatePayroll, PayrollBreakdown } from "../services/payrollService";
import { getStatusCode } from "../services/apiError";

export default function AdminDashboardPage() {
  const [employeeId, setEmployeeId] = useState("");
  const [grossSalary, setGrossSalary] = useState("");
  const [breakdown, setBreakdown] = useState<PayrollBreakdown | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setBreakdown(null);
    setIsCalculating(true);

    try {
      const result = await calculatePayroll(Number(employeeId), Number(grossSalary));
      setBreakdown(result.data);
    } catch (error) {
      const status = getStatusCode(error);
      if (status === 404) {
        setErrorMessage("No existe un empleado con ese ID");
      } else if (status === 400) {
        setErrorMessage("El salario no puede ser negativo");
      } else {
        setErrorMessage("No se pudo calcular la nómina, intenta de nuevo");
      }
    } finally {
      setIsCalculating(false);
    }
  }

  return (
    <PageTransition>
      <div className="dashboard-shell">
        <div className="dashboard-topbar">
          <span className="dashboard-topbar-brand">CEN Payroll</span>
          <button className="logout-link" onClick={handleLogout}>
            Cerrar sesión
          </button>
        </div>

        <motion.div
          className="dashboard-content"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        >
          <div className="dashboard-panel">
            <div className="dashboard-panel-header">
              <h1>Calcular nómina</h1>
              <button
                className="secondary-button"
                onClick={() => navigate("/admin/nuevo-empleado")}
              >
                <UsersIcon />
                Dar de alta empleado
              </button>
            </div>

            <AnimatePresence mode="wait">
              {errorMessage && <ErrorMessage key="error" message={errorMessage} />}
            </AnimatePresence>

            <form className="payroll-form" onSubmit={handleSubmit}>
              <FormField
                id="employeeId"
                label="ID del empleado"
                type="number"
                value={employeeId}
                onChange={setEmployeeId}
                min={1}
                required
              />
              <FormField
                id="grossSalary"
                label="Salario bruto mensual"
                type="number"
                value={grossSalary}
                onChange={setGrossSalary}
                min={0}
                step={0.01}
                required
              />
              <SubmitButton
                label="Calcular"
                loadingLabel="Calculando..."
                isLoading={isCalculating}
              />
            </form>

            <AnimatePresence mode="wait">
              {breakdown && <PayrollResultCard key="result" breakdown={breakdown} />}
            </AnimatePresence>
          </div>
        </motion.div>
      </div>
    </PageTransition>
  );
}
