import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence } from "motion/react";
import { ArrowLeft, Buildings, EnvelopeSimple, UserCirclePlus, UsersThree } from "@phosphor-icons/react";
import CompanyFields from "../components/CompanyFields";
import FormField from "../components/FormField";
import ErrorMessage from "../components/ErrorMessage";
import SuccessMessage from "../components/SuccessMessage";
import SubmitButton from "../components/SubmitButton";
import Skeleton from "../components/Skeleton";
import TemporaryPassword from "../components/TemporaryPassword";
import { CompanyInput, companyMeta, toCompanyInput } from "../services/companyData";
import {
  assignAdmin,
  inviteAdmin,
  listOwnerCompanies,
  OwnerCompany,
  RiskPremium,
  setOwnerCompanyActive,
  setRiskPremium,
  unassignAdmin,
  updateOwnerCompany
} from "../services/ownerService";
import { getStatusCode } from "../services/apiError";
import { formatDate, formatInteger } from "../services/format";
import "../styles/skin-dueno.css";

type Mode =
  | { kind: "idle" }
  | { kind: "edit"; companyId: number; form: CompanyInput }
  | { kind: "toggle"; companyId: number }
  | { kind: "invite"; companyId: number; name: string; email: string }
  | { kind: "assign"; companyId: number; email: string }
  | { kind: "risk"; companyId: number; ratePercent: string; validFrom: string };

const IDLE: Mode = { kind: "idle" };

// La prima llega como fraccion (0.0054355) y se muestra en por ciento, como se declara.
function riskPercent(premium: RiskPremium): string {
  return String(Number((Number(premium.rate) * 100).toFixed(5)));
}

function isAddingAdmin(mode: Mode, companyId: number): boolean {
  return (mode.kind === "invite" || mode.kind === "assign") && mode.companyId === companyId;
}

export default function OwnerCompaniesPage() {
  const navigate = useNavigate();
  const [companies, setCompanies] = useState<OwnerCompany[] | null>(null);
  const [mode, setMode] = useState<Mode>(IDLE);
  const [busy, setBusy] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [issued, setIssued] = useState<{ name: string; password: string } | null>(null);

  useEffect(() => {
    let isMounted = true;
    listOwnerCompanies()
      .then((list) => isMounted && setCompanies(list))
      .catch(() => {
        if (!isMounted) return;
        setCompanies([]);
        setErrorMessage("No se pudieron cargar tus empresas. Recarga la página.");
      });
    return () => {
      isMounted = false;
    };
  }, []);

  function start(next: Mode) {
    setErrorMessage(null);
    setSuccessMessage(null);
    setMode(next);
  }

  function replace(updated: OwnerCompany) {
    setCompanies((current) =>
      (current ?? []).map((item) => (item.id === updated.id ? updated : item))
    );
  }

  async function run(action: () => Promise<void>, failure: (status?: number) => string) {
    setBusy(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      await action();
      setMode(IDLE);
    } catch (error) {
      setErrorMessage(failure(getStatusCode(error)));
    } finally {
      setBusy(false);
    }
  }

  function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (mode.kind !== "edit") return;
    run(
      async () => {
        const updated = await updateOwnerCompany(mode.companyId, mode.form);
        replace(updated);
        setSuccessMessage("Se guardaron los datos de " + updated.legal_name + ".");
      },
      (status) =>
        status === 409
          ? "Ese RFC ya pertenece a otra empresa."
          : status === 422
            ? "Revisa el RFC (12 o 13 caracteres) y el registro patronal (letra y 10 dígitos)."
            : "No se pudieron guardar los datos. Inténtalo de nuevo."
    );
  }

  function handleToggle(company: OwnerCompany) {
    run(
      async () => {
        const updated = await setOwnerCompanyActive(company.id, !company.is_active);
        replace(updated);
        setSuccessMessage(
          updated.is_active
            ? updated.legal_name + " vuelve a operar."
            : updated.legal_name + " quedó desactivada: sus administradores ya no operan su nómina y sus empleados no pueden entrar."
        );
      },
      () => "No se pudo cambiar el estado de la empresa. Inténtalo de nuevo."
    );
  }

  function handleInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (mode.kind !== "invite") return;
    run(
      async () => {
        const invited = await inviteAdmin(mode.companyId, { name: mode.name, email: mode.email });
        replace(invited.company);
        setIssued({ name: mode.name, password: invited.temporary_password });
      },
      (status) =>
        status === 409
          ? "Ese correo ya está registrado. Si ya es administrador, asígnalo por correo."
          : "No se pudo invitar al administrador. Revisa los datos e inténtalo de nuevo."
    );
  }

  function handleAssign(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (mode.kind !== "assign") return;
    run(
      async () => {
        const updated = await assignAdmin(mode.companyId, mode.email);
        replace(updated);
        setSuccessMessage(mode.email + " ya administra " + updated.legal_name + ".");
      },
      (status) =>
        status === 404
          ? "No hay un administrador activo con ese correo. Revísalo o invítalo como nuevo."
          : "No se pudo asignar al administrador. Inténtalo de nuevo."
    );
  }

  function handleRiskPremium(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (mode.kind !== "risk") return;
    run(
      async () => {
        const updated = await setRiskPremium(mode.companyId, {
          ratePercent: mode.ratePercent,
          validFrom: mode.validFrom
        });
        replace(updated);
        setSuccessMessage("Se registró la prima de riesgo de " + updated.legal_name + ".");
      },
      (status) =>
        status === 409
          ? "Ya hay una prima registrada desde esa fecha o después. Elige una fecha posterior."
          : status === 422
            ? "La prima va de 0.5 % a 15 %, con hasta cinco decimales."
            : "No se pudo registrar la prima. Inténtalo de nuevo."
    );
  }

  function handleUnassign(company: OwnerCompany, adminId: number, name: string) {
    run(
      async () => {
        replace(await unassignAdmin(company.id, adminId));
        setSuccessMessage(name + " ya no administra " + company.legal_name + ". Su cuenta sigue activa.");
      },
      () => "No se pudo retirar al administrador. Inténtalo de nuevo."
    );
  }

  return (
    <div className="dashboard-panel">
      <div className="dashboard-panel-header">
        <div className="dashboard-panel-heading">
          <span className="panel-icon-badge" aria-hidden="true">
            <Buildings weight="bold" />
          </span>
          <div>
            <h1>Mis empresas</h1>
            <p className="dashboard-panel-subtitle">
              Corrige sus datos, decide quién administra su nómina y desactívalas si dejan de operar.
              Para registrar una empresa nueva, pídela al administrador de la plataforma.
            </p>
          </div>
        </div>
        <button className="btn btn-line" onClick={() => navigate("/dueno")}>
          <ArrowLeft weight="bold" />
          Volver al tablero
        </button>
      </div>

      <AnimatePresence mode="wait">
        {errorMessage && <ErrorMessage key="error" message={errorMessage} />}
        {successMessage && <SuccessMessage key="success" message={successMessage} />}
      </AnimatePresence>

      <AnimatePresence mode="wait">
        {issued && (
          <TemporaryPassword
            key={issued.password}
            name={issued.name}
            password={issued.password}
            onDismiss={() => setIssued(null)}
          />
        )}
      </AnimatePresence>

      {companies === null && (
        <div className="skeleton-stack" aria-hidden="true">
          <Skeleton height={140} />
          <Skeleton height={140} />
        </div>
      )}

      {companies !== null && companies.length === 0 && !errorMessage && (
        <div className="empty-state">
          <span className="empty-state-icon" aria-hidden="true">
            <Buildings weight="bold" />
          </span>
          <p className="empty-state-title">Todavía no tienes empresas asignadas</p>
          <p>El administrador de la plataforma te las asigna.</p>
        </div>
      )}

      <div className="owner-body">
        {companies?.map((company) => (
          <section
            key={company.id}
            className={company.is_active ? "owner-card" : "owner-card is-inactive"}
            aria-labelledby={"empresa-" + company.id}
          >
            {mode.kind === "edit" && mode.companyId === company.id ? (
              <form className="employee-edit" onSubmit={handleSave}>
                <CompanyFields
                  idPrefix={"empresa-" + company.id}
                  value={mode.form}
                  onChange={(form) => setMode({ ...mode, form })}
                />
                <div className="employee-edit-actions">
                  <SubmitButton label="Guardar cambios" loadingLabel="Guardando…" isLoading={busy} />
                  <button type="button" className="btn btn-line" onClick={() => setMode(IDLE)}>
                    Cancelar
                  </button>
                </div>
              </form>
            ) : (
              <>
                <div className="owner-company-head">
                  <div>
                    <h2 id={"empresa-" + company.id}>
                      {company.legal_name}
                      {!company.is_active && <span className="employee-tag">Inactiva</span>}
                    </h2>
                    <p className="owner-card-note">
                      {companyMeta(company)} · {formatInteger(company.active_employees)}{" "}
                      {company.active_employees === 1 ? "empleado activo" : "empleados activos"}
                    </p>
                  </div>
                  {mode.kind === "toggle" && mode.companyId === company.id ? (
                    <div className="employee-row-confirm">
                      <p>
                        {company.is_active
                          ? "Sus administradores dejarán de operar la nómina y sus empleados no podrán entrar. Los recibos se conservan."
                          : "Sus administradores y empleados vuelven a tener acceso."}
                      </p>
                      <div className="employee-row-actions">
                        <button className="btn btn-rosa" onClick={() => handleToggle(company)} disabled={busy}>
                          {busy ? "Procesando…" : company.is_active ? "Desactivar" : "Reactivar"}
                        </button>
                        <button className="btn btn-line" onClick={() => setMode(IDLE)} disabled={busy}>
                          Cancelar
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="employee-row-actions">
                      <button
                        className="btn btn-line"
                        onClick={() => start({ kind: "edit", companyId: company.id, form: toCompanyInput(company) })}
                      >
                        Editar datos
                      </button>
                      <button
                        className="btn btn-line"
                        onClick={() => start({ kind: "toggle", companyId: company.id })}
                      >
                        {company.is_active ? "Desactivar" : "Reactivar"}
                      </button>
                    </div>
                  )}
                </div>

                <h3 className="owner-subtitle">Prima de riesgo de trabajo</h3>
                {mode.kind === "risk" && mode.companyId === company.id ? (
                  <form className="employee-edit owner-admin-form" onSubmit={handleRiskPremium} aria-label="Registrar prima de riesgo">
                    <FormField
                      id={"prima-" + company.id}
                      label="Prima (%)"
                      type="number"
                      value={mode.ratePercent}
                      onChange={(ratePercent) => setMode({ ...mode, ratePercent })}
                      min={0.5}
                      step={0.00001}
                      inputMode="decimal"
                      hint="La de tu declaración anual. Si la empresa es nueva, la prima media de su clase (clase I: 0.54355 %)."
                      required
                    />
                    <FormField
                      id={"prima-desde-" + company.id}
                      label="Vigente desde"
                      type="date"
                      value={mode.validFrom}
                      onChange={(validFrom) => setMode({ ...mode, validFrom })}
                      hint="Normalmente el 1 de marzo. La prima anterior termina el día previo."
                      required
                    />
                    <div className="employee-edit-actions">
                      <SubmitButton label="Registrar prima" loadingLabel="Guardando…" isLoading={busy} />
                      <button type="button" className="btn btn-line" onClick={() => setMode(IDLE)}>
                        Cancelar
                      </button>
                    </div>
                  </form>
                ) : (
                  <div className="owner-risk">
                    <p className="owner-card-note">
                      {company.risk_premium
                        ? `${riskPercent(company.risk_premium)} % desde el ${formatDate(company.risk_premium.valid_from).toLowerCase()}.`
                        : "Sin prima registrada: el costo patronal no incluye riesgos de trabajo."}
                    </p>
                    {company.is_active && (
                      <button
                        className="btn btn-line"
                        onClick={() =>
                          start({
                            kind: "risk",
                            companyId: company.id,
                            ratePercent: company.risk_premium ? riskPercent(company.risk_premium) : "",
                            validFrom: ""
                          })
                        }
                      >
                        {company.risk_premium ? "Registrar prima nueva" : "Registrar prima"}
                      </button>
                    )}
                  </div>
                )}

                <h3 className="owner-subtitle">Administradores</h3>
                {company.admins.length === 0 ? (
                  <p className="owner-card-note">Nadie administra esta empresa todavía.</p>
                ) : (
                  <ul className="employee-list owner-admins">
                    {company.admins.map((admin) => (
                      <li
                        key={admin.id}
                        className={admin.is_active ? "employee-row" : "employee-row is-inactive"}
                      >
                        <div className="employee-row-main">
                          <p className="employee-row-name">
                            {admin.name}
                            {!admin.is_active && <span className="employee-tag">Cuenta desactivada</span>}
                          </p>
                          <p className="employee-row-meta">{admin.email}</p>
                        </div>
                        <button
                          className="btn btn-line"
                          onClick={() => handleUnassign(company, admin.id, admin.name)}
                          disabled={busy}
                        >
                          Retirar
                        </button>
                      </li>
                    ))}
                  </ul>
                )}

                {mode.kind === "invite" && mode.companyId === company.id && (
                  <form className="employee-edit owner-admin-form" onSubmit={handleInvite} aria-label="Invitar administrador">
                    <FormField
                      id={"invitar-nombre-" + company.id}
                      label="Nombre completo"
                      type="text"
                      value={mode.name}
                      onChange={(name) => setMode({ ...mode, name })}
                      icon={<UsersThree weight="bold" />}
                      required
                    />
                    <FormField
                      id={"invitar-correo-" + company.id}
                      label="Correo"
                      type="email"
                      value={mode.email}
                      onChange={(email) => setMode({ ...mode, email })}
                      inputMode="email"
                      icon={<EnvelopeSimple weight="bold" />}
                      hint="Recibirá una contraseña temporal que cambiará en su primer acceso."
                      required
                    />
                    <div className="employee-edit-actions">
                      <SubmitButton label="Invitar" loadingLabel="Invitando…" isLoading={busy} />
                      <button type="button" className="btn btn-line" onClick={() => setMode(IDLE)}>
                        Cancelar
                      </button>
                    </div>
                  </form>
                )}

                {mode.kind === "assign" && mode.companyId === company.id && (
                  <form className="employee-edit owner-admin-form" onSubmit={handleAssign} aria-label="Asignar administrador">
                    <FormField
                      id={"asignar-correo-" + company.id}
                      label="Correo del administrador"
                      type="email"
                      value={mode.email}
                      onChange={(email) => setMode({ ...mode, email })}
                      inputMode="email"
                      icon={<EnvelopeSimple weight="bold" />}
                      hint="Para alguien que ya administra otra empresa. Escribe su correo exacto."
                      required
                    />
                    <div className="employee-edit-actions">
                      <SubmitButton label="Asignar" loadingLabel="Asignando…" isLoading={busy} />
                      <button type="button" className="btn btn-line" onClick={() => setMode(IDLE)}>
                        Cancelar
                      </button>
                    </div>
                  </form>
                )}

                {company.is_active && !isAddingAdmin(mode, company.id) && (
                  <div className="employee-row-actions owner-admin-actions">
                    <button
                      className="btn btn-line"
                      onClick={() => start({ kind: "invite", companyId: company.id, name: "", email: "" })}
                    >
                      <UserCirclePlus weight="bold" />
                      Invitar administrador
                    </button>
                    <button
                      className="btn btn-line"
                      onClick={() => start({ kind: "assign", companyId: company.id, email: "" })}
                    >
                      Asignar uno existente
                    </button>
                  </div>
                )}
              </>
            )}
          </section>
        ))}
      </div>
    </div>
  );
}
