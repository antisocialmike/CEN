import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence } from "motion/react";
import DashboardTopbar from "../components/DashboardTopbar";
import FormField from "../components/FormField";
import SelectField from "../components/SelectField";
import ErrorMessage from "../components/ErrorMessage";
import SubmitButton from "../components/SubmitButton";
import PayrollResultCard from "../components/PayrollResultCard";
import Skeleton from "../components/Skeleton";
import { Receipt, UsersThree, Wallet } from "@phosphor-icons/react";
import {
  calculatePayroll,
  getRecentReceipts,
  PayrollCalculationResult,
  PayrollReceipt
} from "../services/payrollService";
import { listEmployees, EmployeeCreated } from "../services/employeeService";
import { getStatusCode } from "../services/apiError";
import { formatCurrency, formatDateShort } from "../services/format";

export default function AdminDashboardPage() {
  const [employees, setEmployees] = useState<EmployeeCreated[] | null>(null);
  const [receipts, setReceipts] = useState<PayrollReceipt[] | null>(null);
  const [employeeId, setEmployeeId] = useState("");
  const [grossSalary, setGrossSalary] = useState("");
  const [result, setResult] = useState<PayrollCalculationResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const navigate = useNavigate();

  const selectedEmployee = employees?.find((item) => String(item.id) === employeeId);

  useEffect(() => {
    let isMounted = true;

    listEmployees()
      .then((result) => {
        if (!isMounted) return;
        setEmployees(result);
        if (result.length > 0) {
          setEmployeeId(String(result[0].id));
          setGrossSalary(String(result[0].base_salary));
        }
      })
      .catch(() => {
        if (!isMounted) return;
        setEmployees([]);
        setErrorMessage("No se pudo cargar la lista de empleados. Recarga la página.");
      });

    getRecentReceipts()
      .then((data) => isMounted && setReceipts(data))
      .catch(() => isMounted && setReceipts([]));

    return () => {
      isMounted = false;
    };
  }, []);

  function handleEmployeeChange(nextId: string) {
    setEmployeeId(nextId);
    setResult(null);
    const employee = employees?.find((item) => String(item.id) === nextId);
    if (employee) {
      setGrossSalary(String(employee.base_salary));
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setResult(null);
    setIsCalculating(true);

    try {
      const calculation = await calculatePayroll(Number(employeeId), Number(grossSalary));
      setResult(calculation);
      setReceipts((current) => {
        const row: PayrollReceipt = {
          id: calculation.receipt_id,
          employee_id: calculation.employee_id,
          employee_name: calculation.employee_name ?? selectedEmployee?.name,
          created_at: new Date().toISOString(),
          ...calculation.data
        };
        return [row, ...(current ?? [])].slice(0, 20);
      });
    } catch (error) {
      const status = getStatusCode(error);
      if (status === 404) {
        setErrorMessage("Ese empleado ya no existe. Recarga la página para actualizar la lista.");
      } else if (status === 400) {
        setErrorMessage("El salario bruto no puede ser negativo.");
      } else {
        setErrorMessage("No se pudo calcular la nómina. Revisa tu conexión e inténtalo de nuevo.");
      }
    } finally {
      setIsCalculating(false);
    }
  }

  const hasEmployees = employees !== null && employees.length > 0;

  return (
    <div className="dashboard-shell">
      <a className="skip-link" href="#contenido">
        Ir al contenido
      </a>
      <DashboardTopbar context="Panel de administración" />

      <main className="dashboard-content" id="contenido">
        <div className="dashboard-panel">
          <div className="dashboard-panel-header">
            <div className="dashboard-panel-heading">
              <span className="panel-icon-badge" aria-hidden="true">
                <Wallet weight="bold" />
              </span>
              <div>
                <h1>Calcular nómina</h1>
                <p className="dashboard-panel-subtitle">
                  Cada cálculo genera un recibo con el desglose de ISR e IMSS y queda disponible
                  para el empleado.
                </p>
              </div>
            </div>
            <button
              className="btn btn-line"
              onClick={() => navigate("/admin/nuevo-empleado")}
            >
              <UsersThree weight="bold" />
              Dar de alta empleado
            </button>
          </div>

          <AnimatePresence mode="wait">
            {errorMessage && <ErrorMessage key="error" message={errorMessage} />}
          </AnimatePresence>

          {employees === null && (
            <div className="dashboard-grid">
              <div className="payroll-form skeleton-stack" aria-hidden="true">
                <Skeleton width="30%" height={12} />
                <Skeleton height={44} />
                <Skeleton width="40%" height={12} />
                <Skeleton height={44} />
                <Skeleton height={44} />
              </div>
              <div className="payroll-result skeleton-stack" aria-hidden="true">
                <Skeleton width="45%" height={12} />
                <Skeleton height={16} />
                <Skeleton height={16} />
                <Skeleton height={16} />
                <Skeleton width="60%" height={28} />
              </div>
              <p className="visually-hidden" role="status">
                Cargando empleados
              </p>
            </div>
          )}

          {employees !== null && employees.length === 0 && (
            <div className="empty-state">
              <span className="empty-state-icon" aria-hidden="true">
                <UsersThree weight="bold" />
              </span>
              <p className="empty-state-title">Todavía no hay nadie en la nómina</p>
              <p>
                Da de alta al primer empleado y podrás calcular su ISR e IMSS y emitir su recibo
                en el mismo paso.
              </p>
              <button
                className="btn btn-line"
                onClick={() => navigate("/admin/nuevo-empleado")}
              >
                <UsersThree weight="bold" />
                Dar de alta al primer empleado
              </button>
            </div>
          )}

          {hasEmployees && (
            <>
              <div className="dashboard-grid">
                <form className="payroll-form" onSubmit={handleSubmit}>
                  <SelectField
                    id="employeeId"
                    label="Empleado"
                    value={employeeId}
                    onChange={handleEmployeeChange}
                    options={employees.map((employee) => ({
                      value: String(employee.id),
                      label: employee.name
                    }))}
                    hint={`${employees.length} ${
                      employees.length === 1 ? "persona registrada" : "personas registradas"
                    } en la nómina.`}
                  />
                  <FormField
                    id="grossSalary"
                    label="Salario bruto del periodo"
                    type="number"
                    value={grossSalary}
                    onChange={setGrossSalary}
                    min={0}
                    step={0.01}
                    inputMode="decimal"
                    placeholder="0.00"
                    prefix="$"
                    hint={
                      selectedEmployee
                        ? `Salario base registrado: ${formatCurrency(selectedEmployee.base_salary)}`
                        : undefined
                    }
                    required
                  />
                  <SubmitButton
                    label="Calcular y emitir recibo"
                    loadingLabel="Calculando…"
                    isLoading={isCalculating}
                  />
                </form>

                <AnimatePresence mode="wait">
                  {result ? (
                    <PayrollResultCard key="result" result={result} />
                  ) : (
                    <div className="payroll-result-placeholder" key="placeholder">
                      <Wallet weight="bold" />
                      <p>
                        El desglose de ISR, IMSS y neto a pagar aparecerá aquí en cuanto calcules
                        la nómina.
                      </p>
                    </div>
                  )}
                </AnimatePresence>
              </div>

              <div className="section-title-row">
                <h2 className="section-title">Recibos recientes</h2>
                <p className="section-note">Últimos 20 emitidos por el equipo</p>
              </div>

              {receipts === null && (
                <div className="skeleton-card skeleton-stack" aria-hidden="true">
                  <Skeleton height={16} />
                  <Skeleton height={16} />
                  <Skeleton height={16} />
                </div>
              )}

              {receipts !== null && receipts.length === 0 && (
                <div className="empty-state">
                  <span className="empty-state-icon" aria-hidden="true">
                    <Receipt weight="bold" />
                  </span>
                  <p className="empty-state-title">Aún no se ha emitido ningún recibo</p>
                  <p>El primer cálculo que hagas aparecerá aquí y en el portal del empleado.</p>
                </div>
              )}

              {receipts !== null && receipts.length > 0 && (
                <div className="table-wrap">
                  <table className="data-table">
                    <caption className="visually-hidden">
                      Recibos de nómina emitidos recientemente
                    </caption>
                    <thead>
                      <tr>
                        <th scope="col">Empleado</th>
                        <th scope="col">Fecha</th>
                        <th scope="col" className="num">
                          Bruto
                        </th>
                        <th scope="col" className="num">
                          ISR
                        </th>
                        <th scope="col" className="num">
                          IMSS
                        </th>
                        <th scope="col" className="num">
                          Neto
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {receipts.map((receipt) => (
                        <tr key={receipt.id}>
                          <td className="name">
                            {receipt.employee_name ?? `Empleado #${receipt.employee_id}`}
                          </td>
                          <td>{formatDateShort(receipt.created_at)}</td>
                          <td className="num">{formatCurrency(receipt.gross_salary)}</td>
                          <td className="num">− {formatCurrency(receipt.isr_deduction)}</td>
                          <td className="num">− {formatCurrency(receipt.imss_deduction)}</td>
                          <td className="num net">{formatCurrency(receipt.net_salary)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
