import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import PageTransition from "../components/PageTransition";
import FormField from "../components/FormField";
import SelectField from "../components/SelectField";
import ErrorMessage from "../components/ErrorMessage";
import SubmitButton from "../components/SubmitButton";
import PayrollResultCard from "../components/PayrollResultCard";
import { LogoMark, LogoutIcon, UsersIcon, WalletIcon } from "../components/icons";
import { logout } from "../services/authService";
import { calculatePayroll, PayrollBreakdown } from "../services/payrollService";
import { listEmployees, EmployeeCreated } from "../services/employeeService";
import { getStatusCode } from "../services/apiError";

export default function AdminDashboardPage() {
  const [employees, setEmployees] = useState<EmployeeCreated[] | null>(null);
  const [employeeId, setEmployeeId] = useState("");
  const [grossSalary, setGrossSalary] = useState("");
  const [breakdown, setBreakdown] = useState<PayrollBreakdown | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    async function loadEmployees() {
      try {
        const result = await listEmployees();
        setEmployees(result);
        if (result.length > 0) {
          setEmployeeId(String(result[0].id));
        }
      } catch (error) {
        setEmployees([]);
        setErrorMessage("No se pudo cargar la lista de empleados");
      }
    }

    loadEmployees();
  }, []);

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
        setErrorMessage("Ese empleado ya no existe, actualiza la página");
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
          <div className="brand-logo sm">
            <LogoMark />
            <div className="brand-logo-text">
              <span>CEN Payroll</span>
              <small>Panel de administración</small>
            </div>
          </div>
          <div className="dashboard-topbar-right">
            <span className="user-chip">
              <span className="user-chip-avatar">A</span>
              <span className="user-chip-role">Administrador</span>
            </span>
            <button className="logout-link" onClick={handleLogout}>
              <LogoutIcon />
              Cerrar sesión
            </button>
          </div>
        </div>

        <motion.div
          className="dashboard-content"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        >
          <div className="dashboard-panel">
            <div className="dashboard-panel-header">
              <div className="dashboard-panel-heading">
                <span className="panel-icon-badge">
                  <WalletIcon />
                </span>
                <div>
                  <p className="dashboard-panel-eyebrow">Nómina</p>
                  <h1>Calcular nómina</h1>
                </div>
              </div>
              <button
                className="secondary-button"
                onClick={() => navigate("/admin/nuevo-empleado")}
              >
                <UsersIcon />
                Dar de alta empleado
              </button>
            </div>

            {employees !== null && employees.length > 0 && (
              <div className="stat-row">
                <div className="stat-card">
                  <span className="stat-card-icon">
                    <UsersIcon />
                  </span>
                  <div>
                    <p className="stat-card-label">Empleados registrados</p>
                    <p className="stat-card-value">{employees.length}</p>
                  </div>
                </div>
              </div>
            )}

            <AnimatePresence mode="wait">
              {errorMessage && <ErrorMessage key="error" message={errorMessage} />}
            </AnimatePresence>

            {employees === null && <p className="loading-text">Cargando empleados...</p>}

            {employees !== null && employees.length === 0 && (
              <div className="empty-state">
                <span className="empty-state-icon">
                  <UsersIcon />
                </span>
                <p>Aún no hay empleados registrados. Da de alta al primero para calcular su nómina.</p>
              </div>
            )}

            {employees !== null && employees.length > 0 && (
              <div className="dashboard-grid">
                <form className="payroll-form" onSubmit={handleSubmit}>
                  <SelectField
                    id="employeeId"
                    label="Empleado"
                    value={employeeId}
                    onChange={setEmployeeId}
                    options={employees.map((employee) => ({
                      value: String(employee.id),
                      label: `${employee.name} (#${employee.id})`
                    }))}
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
                  {breakdown ? (
                    <PayrollResultCard key="result" breakdown={breakdown} />
                  ) : (
                    <div className="payroll-result-placeholder" key="placeholder">
                      <WalletIcon />
                      <p>El desglose de ISR, IMSS y neto a pagar aparecerá aquí en cuanto calcules la nómina.</p>
                    </div>
                  )}
                </AnimatePresence>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </PageTransition>
  );
}
