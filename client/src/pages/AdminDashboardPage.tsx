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
  countActiveConcepts,
  emptyConcepts,
  getRecentReceipts,
  PayrollCalculationResult,
  PayrollConcepts,
  PayrollReceipt,
  Periodicity,
  PERIODICITY_LABELS,
  ExistingReceipt,
  lookupReceipt,
  suggestedGrossSalary
} from "../services/payrollService";
import { listEmployees, EmployeeCreated } from "../services/employeeService";
import { getStatusCode } from "../services/apiError";
import {
  currentPeriod,
  formatCurrency,
  formatDateShort,
  periodStartsOf
} from "../services/format";

export default function AdminDashboardPage() {
  const [employees, setEmployees] = useState<EmployeeCreated[] | null>(null);
  const [receipts, setReceipts] = useState<PayrollReceipt[] | null>(null);
  const [employeeId, setEmployeeId] = useState("");
  const [month, setMonth] = useState(currentPeriod());
  const [periodicity, setPeriodicity] = useState<Periodicity>("mensual");
  const [periodStart, setPeriodStart] = useState(currentPeriod() + "-01");
  const [concepts, setConcepts] = useState<PayrollConcepts>(emptyConcepts);
  const [showConcepts, setShowConcepts] = useState(false);
  const [grossSalary, setGrossSalary] = useState("");
  const [result, setResult] = useState<PayrollCalculationResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [pendingReplacement, setPendingReplacement] =
    useState<ExistingReceipt | null>(null);
  const navigate = useNavigate();

  const selectedEmployee = employees?.find((item) => String(item.id) === employeeId);
  const periodOptions = periodStartsOf(periodicity, month);

  const activeConcepts = countActiveConcepts(concepts);

  function changePeriodicity(next: Periodicity) {
    setPeriodicity(next);
    setPendingReplacement(null);
    setPeriodStart(periodStartsOf(next, month)[0]);
    setResult(null);
    setConcepts(emptyConcepts);
    if (selectedEmployee) {
      setGrossSalary(
        String(suggestedGrossSalary(selectedEmployee.base_salary, next))
      );
    }
  }

  function changeMonth(next: string) {
    setMonth(next);
    setPendingReplacement(null);
    setPeriodStart(periodStartsOf(periodicity, next)[0]);
    setResult(null);
  }

  useEffect(() => {
    let isMounted = true;

    listEmployees()
      .then((all) => {
        if (!isMounted) return;
        const result = all.filter((employee) => employee.is_active);
        setEmployees(result);
        if (result.length > 0) {
          setEmployeeId(String(result[0].id));
          setGrossSalary(
            String(suggestedGrossSalary(result[0].base_salary, "mensual"))
          );
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
    setPendingReplacement(null);
    setResult(null);
    setConcepts(emptyConcepts);
    const employee = employees?.find((item) => String(item.id) === nextId);
    if (employee) {
      setGrossSalary(
        String(suggestedGrossSalary(employee.base_salary, periodicity))
      );
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setResult(null);

    if (pendingReplacement === null) {
      setIsCalculating(true);
      try {
        const existing = await lookupReceipt(
          Number(employeeId),
          periodicity,
          periodStart
        );
        if (existing) {
          setPendingReplacement(existing);
          return;
        }
      } catch {
        setErrorMessage(
          "No se pudo comprobar si ya existe un recibo de ese periodo. Inténtalo de nuevo."
        );
        return;
      } finally {
        setIsCalculating(false);
      }
    }

    await emitPayroll();
  }

  async function emitPayroll() {
    setPendingReplacement(null);
    setErrorMessage(null);
    setIsCalculating(true);

    try {
      const calculation = await calculatePayroll(
        Number(employeeId),
        periodicity,
        periodStart,
        Number(grossSalary),
        concepts
      );
      setResult(calculation);
      setReceipts((current) => {
        const row: PayrollReceipt = {
          id: calculation.receipt_id,
          employee_id: calculation.employee_id,
          employee_name: calculation.employee_name ?? selectedEmployee?.name,
          period_start: calculation.period_start,
          period_end: calculation.period_end,
          periodicity,
          paid_days: 0,
          processed_by: calculation.processed_by,
          created_at: new Date().toISOString(),
          ...calculation.data
        };
        const rest = (current ?? []).filter((item) => item.id !== row.id);
        return [row, ...rest].slice(0, 20);
      });
    } catch (error) {
      const status = getStatusCode(error);
      if (status === 404) {
        setErrorMessage("Ese empleado ya no existe. Recarga la página para actualizar la lista.");
      } else if (status === 400) {
        setErrorMessage("El salario bruto no puede ser negativo.");
      } else if (status === 409) {
        setErrorMessage("Esa persona ya tiene un recibo que cubre esos días.");
      } else if (status === 422) {
        setErrorMessage("Revisa el periodo y el salario: alguno tiene un formato inválido.");
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
            <div className="dashboard-panel-actions">
              <button
                className="btn btn-line"
                onClick={() => navigate("/admin/empleados")}
              >
                <UsersThree weight="bold" />
                Empleados
              </button>
              <button
                className="btn btn-line"
                onClick={() => navigate("/admin/nuevo-empleado")}
              >
                Dar de alta empleado
              </button>
            </div>
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
                  <SelectField
                    id="periodicity"
                    label="Periodicidad"
                    value={periodicity}
                    onChange={(value) => changePeriodicity(value as Periodicity)}
                    options={Object.entries(PERIODICITY_LABELS).map(
                      ([value, label]) => ({ value, label })
                    )}
                  />
                  <FormField
                    id="month"
                    label="Mes"
                    type="month"
                    value={month}
                    onChange={changeMonth}
                    required
                  />
                  {periodOptions.length > 1 && (
                    <SelectField
                      id="periodStart"
                      label="Periodo"
                      value={periodStart}
                      onChange={setPeriodStart}
                      options={periodOptions.map((start, index) => ({
                        value: start,
                        label:
                          periodicity === "quincenal"
                            ? `${index === 0 ? "Primera" : "Segunda"} quincena`
                            : `Semana ${index + 1}`
                      }))}
                      hint="Recalcular el mismo periodo reemplaza el recibo anterior."
                    />
                  )}
                  {periodOptions.length === 1 && (
                    <p className="form-note">
                      Recalcular el mismo periodo reemplaza el recibo anterior.
                    </p>
                  )}
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
                        ? periodicity === "mensual"
                          ? `Base mensual: ${formatCurrency(selectedEmployee.base_salary)}`
                          : periodicity === "quincenal"
                            ? `Mitad del base mensual: ${formatCurrency(
                                selectedEmployee.base_salary
                              )} ÷ 2 = ${formatCurrency(
                                selectedEmployee.base_salary / 2
                              )}`
                            : `Prorrateo semanal: ${formatCurrency(
                                selectedEmployee.base_salary
                              )} × 12 ÷ 52 = ${formatCurrency(
                                (selectedEmployee.base_salary * 12) / 52
                              )}`
                        : undefined
                    }
                    required
                  />
                  <div className="payroll-concepts">
                    <button
                      type="button"
                      className="payroll-concepts-toggle"
                      onClick={() => setShowConcepts((current) => !current)}
                      aria-expanded={showConcepts}
                      aria-label={`Otros conceptos ${activeConcepts > 0 ? `(${activeConcepts} activo${activeConcepts === 1 ? "" : "s"})` : ""}`}
                    >
                      <span>Otros conceptos</span>
                      {activeConcepts > 0 && (
                        <span className="payroll-concepts-badge">{activeConcepts}</span>
                      )}
                      <span
                        className={
                          activeConcepts > 0
                            ? "payroll-concepts-hint is-active"
                            : "payroll-concepts-hint"
                        }
                      >
                        {activeConcepts > 0
                          ? `${activeConcepts} concepto${
                              activeConcepts === 1 ? "" : "s"
                            }`
                          : showConcepts
                            ? "Ocultar"
                            : "Opcional"}
                      </span>
                    </button>

                    {showConcepts && (
                      <div className="payroll-concepts-grid">
                        <p className="payroll-concepts-legend">Percepciones</p>
                        <FormField
                          id="overtimeDoubleHours"
                          label="Horas extra dobles"
                          type="number"
                          value={String(concepts.overtimeDoubleHours)}
                          onChange={(value) =>
                            setConcepts({ ...concepts, overtimeDoubleHours: Number(value) })
                          }
                          min={0}
                          step={0.5}
                          inputMode="decimal"
                          hint="Las primeras 9 de la semana se pagan al doble."
                        />
                        <FormField
                          id="overtimeTripleHours"
                          label="Horas extra triples"
                          type="number"
                          value={String(concepts.overtimeTripleHours)}
                          onChange={(value) =>
                            setConcepts({ ...concepts, overtimeTripleHours: Number(value) })
                          }
                          min={0}
                          step={0.5}
                          inputMode="decimal"
                          hint="Las que exceden esas 9 horas."
                        />
                        <FormField
                          id="christmasBonusDays"
                          label="Días de aguinaldo"
                          type="number"
                          value={String(concepts.christmasBonusDays)}
                          onChange={(value) =>
                            setConcepts({ ...concepts, christmasBonusDays: Number(value) })
                          }
                          min={0}
                          step={1}
                          inputMode="numeric"
                          hint="La ley pide 15 días como mínimo."
                        />
                        <FormField
                          id="vacationDays"
                          label="Días de vacaciones"
                          type="number"
                          value={String(concepts.vacationDays)}
                          onChange={(value) =>
                            setConcepts({ ...concepts, vacationDays: Number(value) })
                          }
                          min={0}
                          step={1}
                          inputMode="numeric"
                          hint="La prima vacacional es el 25% de esos días."
                        />
                        <FormField
                          id="bonus"
                          label="Bono o gratificación"
                          type="number"
                          value={String(concepts.bonus)}
                          onChange={(value) =>
                            setConcepts({ ...concepts, bonus: Number(value) })
                          }
                          min={0}
                          step={0.01}
                          inputMode="decimal"
                          prefix="$"
                        />

                        <p className="payroll-concepts-legend">Deducciones</p>
                        <FormField
                          id="loanDeduction"
                          label="Préstamo"
                          type="number"
                          value={String(concepts.loanDeduction)}
                          onChange={(value) =>
                            setConcepts({ ...concepts, loanDeduction: Number(value) })
                          }
                          min={0}
                          step={0.01}
                          inputMode="decimal"
                          prefix="$"
                        />
                        <FormField
                          id="housingCreditDeduction"
                          label="Crédito Infonavit"
                          type="number"
                          value={String(concepts.housingCreditDeduction)}
                          onChange={(value) =>
                            setConcepts({
                              ...concepts,
                              housingCreditDeduction: Number(value)
                            })
                          }
                          min={0}
                          step={0.01}
                          inputMode="decimal"
                          prefix="$"
                        />
                      </div>
                    )}
                  </div>

                  {pendingReplacement && (
                    <div className="replace-warning" role="alert">
                      <p className="replace-warning-title">
                        Se reemplazará el recibo de {selectedEmployee?.name}
                      </p>
                      <div className="replace-warning-details">
                        <p className="replace-warning-note">
                          Recibo actual: #{pendingReplacement.id}
                          <br />
                          Neto: {formatCurrency(pendingReplacement.net_salary)}
                        </p>
                        <p className="replace-warning-caution">
                          Al continuar, el empleado verá el nuevo recibo en su portal.
                          El anterior no se puede recuperar.
                        </p>
                      </div>
                      <div className="replace-warning-actions">
                        <button
                          type="button"
                          className="btn btn-line"
                          onClick={() => setPendingReplacement(null)}
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                  )}

                  <SubmitButton
                    label={
                      pendingReplacement
                        ? "Reemplazar el recibo"
                        : "Calcular y emitir recibo"
                    }
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
