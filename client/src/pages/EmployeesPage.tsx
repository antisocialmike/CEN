import { FormEvent, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import { rowVariants, stackVariants, useStill } from "../motion/variants";
import { ArrowLeft, UsersThree } from "@phosphor-icons/react";
import FormField from "../components/FormField";
import SelectField from "../components/SelectField";
import ErrorMessage from "../components/ErrorMessage";
import SuccessMessage from "../components/SuccessMessage";
import SubmitButton from "../components/SubmitButton";
import Skeleton from "../components/Skeleton";
import TemporaryPassword from "../components/TemporaryPassword";
import Paginacion from "../components/Paginacion";
import {
  activateEmployee,
  deactivateEmployee,
  EmployeeCreated,
  getSalaryHistory,
  isAssimilated,
  listEmployeesPage,
  missingFiscalData,
  SalaryChange,
  TIPO_JORNADA_LABELS,
  TIPO_REGIMEN_LABELS,
  TipoJornada,
  TipoRegimen,
  resetEmployeePassword,
  updateEmployee
} from "../services/employeeService";
import { getEmployeeId, EmployeeRole } from "../services/authSession";
import { getErrorDetail, getStatusCode, getValidationMessage } from "../services/apiError";
import { currentDate, formatCurrency, formatDate } from "../services/format";
import { useListaPaginada } from "../routes/listaPaginada";

interface EditForm {
  name: string;
  email: string;
  role: EmployeeRole;
  baseSalary: string;
  tipoRegimen: TipoRegimen;
  tipoJornada: TipoJornada;
  hireDate: string;
  rfc: string;
  curp: string;
  nss: string;
  salaryValidFrom: string;
}

interface IssuedPassword {
  name: string;
  password: string;
}

export default function EmployeesPage() {
  const stackTravel = useStill(stackVariants);
  const rowTravel = useStill(rowVariants);
  const lista = useListaPaginada(listEmployeesPage);
  const employees = lista.items;
  const inicioDeLista = useRef<HTMLUListElement>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<EditForm | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [confirmingResetId, setConfirmingResetId] = useState<number | null>(null);
  const [confirmingToggleId, setConfirmingToggleId] = useState<number | null>(null);
  const [pendingEditSave, setPendingEditSave] = useState(false);
  const [issuedPassword, setIssuedPassword] = useState<IssuedPassword | null>(null);
  const [salaryHistory, setSalaryHistory] = useState<SalaryChange[] | null>(null);
  const [salaryHistoryFailed, setSalaryHistoryFailed] = useState(false);
  const confirmResetRef = useRef<HTMLButtonElement>(null);
  const ownEmployeeId = getEmployeeId();
  // El fallo al cargar no se borra al intentar otra accion: la lista sigue sin llegar.
  const shownError =
    errorMessage ??
    (lista.fallo ? "No se pudo cargar la lista de usuarios. Recarga la página." : null);
  const navigate = useNavigate();

  useEffect(() => {
    if (confirmingResetId !== null) confirmResetRef.current?.focus();
  }, [confirmingResetId]);

  useEffect(() => {
    if (editingId === null) return;
    let current = true;
    getSalaryHistory(editingId)
      .then((history) => {
        if (current) setSalaryHistory(history);
      })
      .catch(() => {
        if (current) setSalaryHistoryFailed(true);
      });
    return () => {
      current = false;
    };
  }, [editingId]);

  function replaceEmployee(updated: EmployeeCreated) {
    lista.actualizar((current) =>
      current.map((item) => (item.id === updated.id ? updated : item))
    );
  }

  function startEditing(employee: EmployeeCreated) {
    setErrorMessage(null);
    setSuccessMessage(null);
    setConfirmingResetId(null);
    setSalaryHistory(null);
    setSalaryHistoryFailed(false);
    setEditingId(employee.id);
    setForm({
      name: employee.name,
      email: employee.email,
      role: employee.role,
      baseSalary: employee.base_salary === null ? "" : String(employee.base_salary),
      tipoRegimen: employee.tipo_regimen ?? "02",
      tipoJornada: employee.tipo_jornada ?? "01",
      hireDate: employee.hire_date ?? "",
      rfc: employee.rfc ?? "",
      curp: employee.curp ?? "",
      nss: employee.nss ?? "",
      salaryValidFrom: currentDate()
    });
  }

  function cancelEditing() {
    setEditingId(null);
    setForm(null);
  }

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (editingId === null || form === null) return;

    const employee = employees?.find((e) => e.id === editingId);
    if (!employee) return;

    const newSalary = form.baseSalary === "" ? null : Number(form.baseSalary);
    const emailChanged = employee.email !== form.email;
    const salaryChanged = employee.base_salary !== newSalary;
    const roleChanged = employee.role !== form.role;
    // Cambiar el tipo de nomina cambia lo que se le retiene: pide confirmacion.
    const regimeChanged = (employee.tipo_regimen ?? "02") !== form.tipoRegimen;
    const hireDateChanged = (employee.hire_date ?? "") !== form.hireDate;

    if (
      (emailChanged || salaryChanged || roleChanged || regimeChanged || hireDateChanged) &&
      !pendingEditSave
    ) {
      setPendingEditSave(true);
      return;
    }

    setPendingEditSave(false);
    setErrorMessage(null);
    setSuccessMessage(null);
    setIsSaving(true);

    try {
      const updated = await updateEmployee(editingId, {
        name: form.name,
        email: form.email,
        role: form.role,
        baseSalary: newSalary,
        tipoRegimen: form.tipoRegimen,
        tipoJornada: form.tipoJornada,
        hireDate: form.hireDate || null,
        rfc: form.rfc,
        curp: form.curp,
        nss: form.tipoRegimen === "02" ? form.nss : "",
        salaryValidFrom: salaryChanged ? form.salaryValidFrom || null : null
      });
      replaceEmployee(updated);
      setSuccessMessage("Se guardaron los cambios de " + updated.name + ".");
      cancelEditing();
    } catch (error) {
      const status = getStatusCode(error);
      const detail = getErrorDetail(error);
      if (status === 409 && detail && detail !== "El correo ya está registrado") {
        setErrorMessage(detail);
      } else if (status === 409) {
        setErrorMessage("Ese correo ya lo usa otra persona. Elige uno distinto.");
      } else if (status === 422 && getValidationMessage(error)) {
        setErrorMessage(getValidationMessage(error) ?? null);
      } else if (status === 400) {
        setErrorMessage("No puedes quitarte a ti mismo el rol de administrador.");
      } else if (status === 404) {
        setErrorMessage("Esa persona ya no existe. Recarga la página.");
      } else {
        setErrorMessage("No se pudieron guardar los cambios. Inténtalo de nuevo.");
      }
    } finally {
      setIsSaving(false);
    }
  }

  function askResetPassword(employee: EmployeeCreated) {
    setErrorMessage(null);
    setSuccessMessage(null);
    cancelEditing();
    setConfirmingResetId(employee.id);
  }

  async function handleResetPassword(employee: EmployeeCreated) {
    setErrorMessage(null);
    setBusyId(employee.id);

    try {
      const reset = await resetEmployeePassword(employee.id);
      setIssuedPassword({ name: reset.name, password: reset.temporary_password });
    } catch (error) {
      if (getStatusCode(error) === 400) {
        setErrorMessage("Tu propia contraseña se cambia desde el botón Contraseña de la barra superior.");
      } else {
        setErrorMessage("No se pudo restablecer la contraseña. Inténtalo de nuevo.");
      }
    } finally {
      setBusyId(null);
      setConfirmingResetId(null);
    }
  }

  function askToggleActive(employee: EmployeeCreated) {
    setErrorMessage(null);
    setSuccessMessage(null);
    setConfirmingResetId(null);
    setConfirmingToggleId(employee.id);
  }

  async function confirmToggleActive(employee: EmployeeCreated) {
    setErrorMessage(null);
    setSuccessMessage(null);
    setBusyId(employee.id);

    try {
      const updated = employee.is_active
        ? await deactivateEmployee(employee.id)
        : await activateEmployee(employee.id);
      replaceEmployee(updated);
      setSuccessMessage(
        updated.is_active
          ? updated.name + " vuelve a estar activa en la nómina."
          : updated.name + " quedó fuera de la nómina. Sus recibos se conservan."
      );
    } catch (error) {
      if (getStatusCode(error) === 400) {
        setErrorMessage("No puedes desactivar tu propia cuenta.");
      } else {
        setErrorMessage("No se pudo cambiar el estado. Inténtalo de nuevo.");
      }
    } finally {
      setBusyId(null);
      setConfirmingToggleId(null);
    }
  }

  return (
    <div className="dashboard-panel">
      <div className="dashboard-panel-header">
        <div className="dashboard-panel-heading">
          <div>
            <h1>Usuarios</h1>
            <p className="dashboard-panel-subtitle">
              Corrige datos, ajusta salarios y da de baja a quien deje la empresa. Dar de baja
              no borra sus recibos.
            </p>
          </div>
        </div>
        <button className="btn btn-line" onClick={() => navigate("/admin")}>
          <ArrowLeft weight="bold" />
          Volver al panel
        </button>
      </div>

      <AnimatePresence mode="wait">
        {shownError && <ErrorMessage key="error" message={shownError} />}
        {successMessage && <SuccessMessage key="success" message={successMessage} />}
      </AnimatePresence>

      <AnimatePresence mode="wait">
        {issuedPassword && (
          <TemporaryPassword
            key={issuedPassword.password}
            name={issuedPassword.name}
            password={issuedPassword.password}
            onDismiss={() => setIssuedPassword(null)}
          />
        )}
      </AnimatePresence>

      {employees === null && (
        <div className="skeleton-stack" aria-hidden="true">
          <Skeleton height={64} />
          <Skeleton height={64} />
          <Skeleton height={64} />
        </div>
      )}

      {employees !== null && employees.length === 0 && (
        <div className="empty-state">
          <span className="empty-state-icon" aria-hidden="true">
            <UsersThree weight="bold" />
          </span>
          <p className="empty-state-title">Todavía no hay nadie en la nómina</p>
          <button className="btn btn-rosa" onClick={() => navigate("/admin/nuevo-usuario")}>
            Dar de alta al primer usuario
          </button>
        </div>
      )}

      {employees !== null && employees.length > 0 && (
        <motion.ul
          ref={inicioDeLista}
          className="employee-list"
          variants={stackTravel}
          initial="initial"
          animate="animate"
        >
          {employees.map((employee) => (
            <motion.li
              key={employee.id}
              variants={rowTravel}
              className={employee.is_active ? "employee-row" : "employee-row is-inactive"}
            >
              {editingId === employee.id && form !== null ? (
                <form className="employee-edit" onSubmit={handleSave}>
                  <FormField
                    id={"name-" + employee.id}
                    label="Nombre completo"
                    type="text"
                    value={form.name}
                    onChange={(value) => setForm({ ...form, name: value })}
                    required
                  />
                  <FormField
                    id={"email-" + employee.id}
                    label="Correo"
                    type="email"
                    value={form.email}
                    onChange={(value) => setForm({ ...form, email: value })}
                    inputMode="email"
                    required
                  />
                  <SelectField
                    id={"role-" + employee.id}
                    label="Rol"
                    value={form.role}
                    onChange={(value) => setForm({ ...form, role: value as EmployeeRole })}
                    options={[
                      { value: "employee", label: "Empleado" },
                      { value: "admin", label: "Administrador" }
                    ]}
                  />
                  <FormField
                    id={"salary-" + employee.id}
                    label="Salario base mensual"
                    type="number"
                    value={form.baseSalary}
                    onChange={(value) => setForm({ ...form, baseSalary: value })}
                    min={0}
                    step={0.01}
                    inputMode="decimal"
                    prefix="$"
                    required={form.role === "employee"}
                    hint={
                      form.role === "admin"
                        ? "Déjalo vacío si administra la nómina pero no la cobra."
                        : undefined
                    }
                  />
                  <SelectField
                    id={"regimen-" + employee.id}
                    label="Tipo de nómina"
                    value={form.tipoRegimen}
                    onChange={(value) => setForm({ ...form, tipoRegimen: value as TipoRegimen })}
                    options={Object.entries(TIPO_REGIMEN_LABELS).map(([value, label]) => ({
                      value,
                      label
                    }))}
                    hint={
                      form.tipoRegimen === "09"
                        ? "Sin IMSS ni subsidio, y sin horas extra, aguinaldo ni prima vacacional."
                        : undefined
                    }
                  />
                  {form.tipoRegimen === "02" && (
                    <SelectField
                      id={"jornada-" + employee.id}
                      label="Jornada"
                      value={form.tipoJornada}
                      onChange={(value) => setForm({ ...form, tipoJornada: value as TipoJornada })}
                      options={Object.entries(TIPO_JORNADA_LABELS).map(([value, label]) => ({
                        value,
                        label
                      }))}
                    />
                  )}
                  <FormField
                    id={"hireDate-" + employee.id}
                    label="Fecha de ingreso"
                    type="date"
                    value={form.hireDate}
                    onChange={(value) => setForm({ ...form, hireDate: value })}
                  />
                  {form.baseSalary !== "" && Number(form.baseSalary) !== employee.base_salary && (
                    <FormField
                      id={"salaryValidFrom-" + employee.id}
                      label="Salario vigente desde"
                      type="date"
                      value={form.salaryValidFrom}
                      onChange={(value) => setForm({ ...form, salaryValidFrom: value })}
                      hint="Queda en su historial de salario con esta fecha."
                      required
                    />
                  )}
                  <FormField
                    id={"rfc-" + employee.id}
                    label="RFC"
                    type="text"
                    value={form.rfc}
                    onChange={(value) => setForm({ ...form, rfc: value.toUpperCase() })}
                    maxLength={13}
                  />
                  <FormField
                    id={"curp-" + employee.id}
                    label="CURP"
                    type="text"
                    value={form.curp}
                    onChange={(value) => setForm({ ...form, curp: value.toUpperCase() })}
                    maxLength={18}
                  />
                  {form.tipoRegimen === "02" && (
                    <FormField
                      id={"nss-" + employee.id}
                      label="NSS"
                      type="text"
                      value={form.nss}
                      onChange={(value) => setForm({ ...form, nss: value })}
                      inputMode="numeric"
                      maxLength={11}
                    />
                  )}
                  <div aria-live="polite">
                    <div className="payroll-result-row is-group">
                      <span>Historial de salario</span>
                      <span />
                    </div>
                    {salaryHistory === null && !salaryHistoryFailed && (
                      <p className="form-field-hint">Cargando…</p>
                    )}
                    {salaryHistoryFailed && (
                      <p className="form-field-hint">No se pudo cargar el historial.</p>
                    )}
                    {salaryHistory !== null && salaryHistory.length === 0 && (
                      <p className="form-field-hint">Sin cambios registrados.</p>
                    )}
                    {salaryHistory?.map((change) => (
                      <div
                        className="payroll-result-row is-item"
                        key={change.valid_from + change.recorded_at}
                      >
                        <span>Desde {formatDate(change.valid_from)}</span>
                        <span>{formatCurrency(change.base_salary)}</span>
                      </div>
                    ))}
                  </div>
                  {pendingEditSave && (
                    <div className="action-confirm" role="alert">
                      <p className="action-confirm-message">Se guardarán cambios importantes.</p>
                      <div className="action-confirm-actions">
                        <button
                          type="button"
                          className="btn btn-line"
                          onClick={() => setPendingEditSave(false)}
                          disabled={isSaving}
                        >
                          Cancelar
                        </button>
                        <button
                          type="submit"
                          className="btn btn-rosa"
                          disabled={isSaving}
                        >
                          {isSaving ? "Guardando…" : "Confirmar"}
                        </button>
                      </div>
                    </div>
                  )}
                  {!pendingEditSave && (
                    <div className="employee-edit-actions">
                      <SubmitButton
                        label="Guardar cambios"
                        loadingLabel="Guardando…"
                        isLoading={isSaving}
                      />
                      <button type="button" className="btn btn-line" onClick={cancelEditing}>
                        Cancelar
                      </button>
                    </div>
                  )}
                </form>
              ) : (
                <>
                  <div className="employee-row-main">
                    <p className="employee-row-name">
                      {employee.name}
                      {!employee.is_active && (
                        <span className="employee-tag">Dado de baja</span>
                      )}
                      {employee.role === "admin" && (
                        <span className="employee-tag is-role">Administrador</span>
                      )}
                      {isAssimilated(employee) && (
                        <span className="employee-tag is-role">Asimilado</span>
                      )}
                      {employee.is_active &&
                        employee.base_salary !== null &&
                        missingFiscalData(employee) && (
                          <span className="employee-tag">Faltan datos fiscales</span>
                        )}
                    </p>
                    <p className="employee-row-meta">
                      {employee.email} ·{" "}
                      {employee.base_salary === null
                        ? "Sin salario en nómina"
                        : formatCurrency(employee.base_salary)}
                    </p>
                  </div>
                  {confirmingResetId === employee.id ? (
                    <div className="employee-row-confirm">
                      <p>La contraseña actual de {employee.name} dejará de funcionar.</p>
                      <div className="employee-row-actions">
                        <button
                          ref={confirmResetRef}
                          className="btn btn-rosa"
                          onClick={() => handleResetPassword(employee)}
                          disabled={busyId === employee.id}
                        >
                          {busyId === employee.id ? "Restableciendo…" : "Restablecer"}
                        </button>
                        <button
                          className="btn btn-line"
                          onClick={() => setConfirmingResetId(null)}
                          disabled={busyId === employee.id}
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                  ) : confirmingToggleId === employee.id ? (
                    <div className="employee-row-confirm">
                      <p>
                        {employee.is_active
                          ? employee.name + " quedará fuera de la nómina. Sus recibos se conservan."
                          : employee.name + " volverá a estar activa en la nómina."}
                      </p>
                      <div className="employee-row-actions">
                        <button
                          className="btn btn-rosa"
                          onClick={() => confirmToggleActive(employee)}
                          disabled={busyId === employee.id}
                        >
                          {busyId === employee.id ? "Procesando…" : employee.is_active ? "Dar de baja" : "Reactivar"}
                        </button>
                        <button
                          className="btn btn-line"
                          onClick={() => setConfirmingToggleId(null)}
                          disabled={busyId === employee.id}
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="employee-row-actions">
                      <button
                        className="btn btn-line"
                        onClick={() => startEditing(employee)}
                        disabled={busyId === employee.id}
                      >
                        Editar
                      </button>
                      {employee.id !== ownEmployeeId && (
                        <>
                          <button
                            className="btn btn-line"
                            onClick={() => askResetPassword(employee)}
                            disabled={busyId === employee.id}
                          >
                            Restablecer contraseña
                          </button>
                          <button
                            className="btn btn-line"
                            onClick={() => askToggleActive(employee)}
                            disabled={busyId === employee.id}
                          >
                            {employee.is_active ? "Dar de baja" : "Reactivar"}
                          </button>
                        </>
                      )}
                    </div>
                  )}
                </>
              )}
            </motion.li>
          ))}
        </motion.ul>
      )}

      <Paginacion
        pagina={lista.pagina}
        total={lista.total}
        porPagina={lista.porPagina}
        etiqueta="Páginas de usuarios"
        alCambiar={lista.irAPagina}
        destino={inicioDeLista}
      />
    </div>
  );
}
