import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import { Buildings, Plus, UsersThree, X } from "@phosphor-icons/react";
import { rowVariants, stackVariants, useStill } from "../motion/variants";
import FormField from "../components/FormField";
import SelectField from "../components/SelectField";
import ErrorMessage from "../components/ErrorMessage";
import SuccessMessage from "../components/SuccessMessage";
import SubmitButton from "../components/SubmitButton";
import Skeleton from "../components/Skeleton";
import {
  assignCompanyOwner,
  Company,
  CompanyInput,
  createCompany,
  ENTIDADES_FEDERATIVAS,
  EntidadFederativa,
  listCompanies,
  listOwners,
  Owner,
  unassignCompanyOwner,
  updateCompany
} from "../services/superadminService";
import { getErrorDetail, getStatusCode } from "../services/apiError";

const emptyCompany: CompanyInput = {
  legalName: "",
  tradeName: "",
  rfc: "",
  registroPatronal: "",
  entidadFederativa: ""
};

const ENTIDAD_OPTIONS = [
  { value: "", label: "Sin definir" },
  ...ENTIDADES_FEDERATIVAS.map((entidad) => ({ value: entidad.value, label: entidad.label }))
];

function entidadLabel(value: EntidadFederativa | null): string | null {
  return ENTIDADES_FEDERATIVAS.find((entidad) => entidad.value === value)?.label ?? null;
}

function companyMeta(company: Company): string {
  const parts = [
    company.trade_name,
    company.rfc ? "RFC " + company.rfc : "Sin RFC",
    entidadLabel(company.entidad_federativa)
  ];
  return parts.filter(Boolean).join(" · ");
}

function toInput(company: Company): CompanyInput {
  return {
    legalName: company.legal_name,
    tradeName: company.trade_name ?? "",
    rfc: company.rfc ?? "",
    registroPatronal: company.registro_patronal ?? "",
    entidadFederativa: company.entidad_federativa ?? ""
  };
}

function saveErrorMessage(error: unknown): string {
  const status = getStatusCode(error);
  if (status === 409) return "Ese RFC ya pertenece a otra empresa.";
  if (status === 422) return "Revisa el RFC (12 o 13 caracteres) y el registro patronal (letra y 10 dígitos).";
  if (status === 404) return "El dueño elegido ya no está activo. Recarga la página.";
  return "No se pudieron guardar los datos de la empresa. Inténtalo de nuevo.";
}

interface CompanyFieldsProps {
  idPrefix: string;
  value: CompanyInput;
  onChange: (value: CompanyInput) => void;
}

function CompanyFields({ idPrefix, value, onChange }: CompanyFieldsProps) {
  return (
    <>
      <FormField
        id={idPrefix + "-legal-name"}
        label="Razón social"
        type="text"
        value={value.legalName}
        onChange={(legalName) => onChange({ ...value, legalName })}
        placeholder="Grupo Norte SA de CV"
        maxLength={200}
        required
      />
      <FormField
        id={idPrefix + "-trade-name"}
        label="Nombre comercial"
        type="text"
        value={value.tradeName}
        onChange={(tradeName) => onChange({ ...value, tradeName })}
        maxLength={150}
      />
      <FormField
        id={idPrefix + "-rfc"}
        label="RFC"
        type="text"
        value={value.rfc}
        onChange={(rfc) => onChange({ ...value, rfc: rfc.toUpperCase() })}
        maxLength={13}
        hint="Opcional por ahora. 12 caracteres para persona moral, 13 para física."
      />
      <FormField
        id={idPrefix + "-registro-patronal"}
        label="Registro patronal IMSS"
        type="text"
        value={value.registroPatronal}
        onChange={(registroPatronal) =>
          onChange({ ...value, registroPatronal: registroPatronal.toUpperCase() })
        }
        maxLength={11}
      />
      <SelectField
        id={idPrefix + "-entidad"}
        label="Estado"
        value={value.entidadFederativa}
        onChange={(entidad) =>
          onChange({ ...value, entidadFederativa: entidad as EntidadFederativa | "" })
        }
        options={ENTIDAD_OPTIONS}
        hint="Define el impuesto estatal sobre nómina."
      />
    </>
  );
}

export default function SuperadminCompaniesPage() {
  const stackTravel = useStill(stackVariants);
  const rowTravel = useStill(rowVariants);
  const navigate = useNavigate();
  const [companies, setCompanies] = useState<Company[] | null>(null);
  const [owners, setOwners] = useState<Owner[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [newCompany, setNewCompany] = useState<CompanyInput>(emptyCompany);
  const [firstOwnerId, setFirstOwnerId] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<CompanyInput>(emptyCompany);
  const [ownerToAssign, setOwnerToAssign] = useState<Record<number, string>>({});
  const [busyId, setBusyId] = useState<number | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const activeOwners = owners.filter((owner) => owner.is_active);

  useEffect(() => {
    let isMounted = true;

    Promise.all([listCompanies(), listOwners()])
      .then(([companyList, ownerList]) => {
        if (!isMounted) return;
        setCompanies(companyList);
        setOwners(ownerList);
      })
      .catch(() => {
        if (!isMounted) return;
        setCompanies([]);
        setErrorMessage("No se pudo cargar la lista de empresas. Recarga la página.");
      });

    return () => {
      isMounted = false;
    };
  }, []);

  function clearMessages() {
    setErrorMessage(null);
    setSuccessMessage(null);
  }

  function replaceCompany(updated: Company) {
    setCompanies((current) =>
      (current ?? []).map((item) => (item.id === updated.id ? updated : item))
    );
  }

  function openCreate() {
    clearMessages();
    setEditingId(null);
    setFirstOwnerId(activeOwners[0] ? String(activeOwners[0].id) : "");
    setIsCreating(true);
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!firstOwnerId) return;
    clearMessages();
    setIsSaving(true);

    try {
      const created = await createCompany(newCompany, Number(firstOwnerId));
      setCompanies((current) => [created, ...(current ?? [])]);
      setSuccessMessage(created.legal_name + " quedó registrada.");
      setNewCompany(emptyCompany);
      setIsCreating(false);
    } catch (error) {
      setErrorMessage(saveErrorMessage(error));
    } finally {
      setIsSaving(false);
    }
  }

  function startEditing(company: Company) {
    clearMessages();
    setIsCreating(false);
    setEditingId(company.id);
    setEditForm(toInput(company));
  }

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (editingId === null) return;
    clearMessages();
    setIsSaving(true);

    try {
      const updated = await updateCompany(editingId, editForm);
      replaceCompany(updated);
      setSuccessMessage("Se guardaron los datos de " + updated.legal_name + ".");
      setEditingId(null);
    } catch (error) {
      setErrorMessage(saveErrorMessage(error));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleAssign(company: Company) {
    const ownerId = Number(ownerToAssign[company.id]);
    if (!ownerId) return;
    clearMessages();
    setBusyId(company.id);

    try {
      replaceCompany(await assignCompanyOwner(company.id, ownerId));
      setOwnerToAssign((current) => ({ ...current, [company.id]: "" }));
    } catch {
      setErrorMessage("No se pudo asignar al dueño. Recarga la página e inténtalo de nuevo.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleUnassign(company: Company, ownerId: number) {
    clearMessages();
    setBusyId(company.id);

    try {
      replaceCompany(await unassignCompanyOwner(company.id, ownerId));
    } catch (error) {
      setErrorMessage(
        getStatusCode(error) === 409
          ? (getErrorDetail(error) ?? company.legal_name + " se quedaría sin dueño activo") +
              ". Asigna otro dueño antes de quitar a este."
          : "No se pudo quitar al dueño. Inténtalo de nuevo."
      );
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="dashboard-panel">
      <div className="dashboard-panel-header">
        <div className="dashboard-panel-heading">
          <span className="panel-icon-badge" aria-hidden="true">
            <Buildings weight="bold" />
          </span>
          <div>
            <h1>Empresas</h1>
            <p className="dashboard-panel-subtitle">
              Registra las empresas y asígnales uno o varios dueños. Toda empresa activa necesita
              al menos un dueño activo.
            </p>
          </div>
        </div>
        <div className="dashboard-panel-actions">
          <button className="btn btn-line" onClick={() => navigate("/superadmin")}>
            <UsersThree weight="bold" />
            Dueños
          </button>
          {!isCreating && (
            <button className="btn btn-rosa" onClick={openCreate}>
              <Plus weight="bold" />
              Nueva empresa
            </button>
          )}
        </div>
      </div>

      <AnimatePresence mode="wait">
        {errorMessage && <ErrorMessage key="error" message={errorMessage} />}
        {successMessage && <SuccessMessage key="success" message={successMessage} />}
      </AnimatePresence>

      {isCreating && activeOwners.length === 0 && (
        <div className="empty-state">
          <p className="empty-state-title">Primero da de alta a un dueño</p>
          <p>Cada empresa nace con al menos un dueño activo.</p>
          <button className="btn btn-rosa" onClick={() => navigate("/superadmin")}>
            Ir a dueños
          </button>
        </div>
      )}

      {isCreating && activeOwners.length > 0 && (
        <form className="employee-edit" onSubmit={handleCreate} aria-label="Nueva empresa">
          <CompanyFields idPrefix="new" value={newCompany} onChange={setNewCompany} />
          <SelectField
            id="new-owner"
            label="Dueño"
            value={firstOwnerId}
            onChange={setFirstOwnerId}
            options={activeOwners.map((owner) => ({ value: String(owner.id), label: owner.name }))}
            hint="Podrás sumar más dueños después."
          />
          <div className="employee-edit-actions">
            <SubmitButton label="Registrar empresa" loadingLabel="Guardando…" isLoading={isSaving} />
            <button type="button" className="btn btn-line" onClick={() => setIsCreating(false)}>
              Cancelar
            </button>
          </div>
        </form>
      )}

      {companies === null && (
        <div className="skeleton-stack" aria-hidden="true">
          <Skeleton height={88} />
          <Skeleton height={88} />
        </div>
      )}

      {companies !== null && companies.length === 0 && !isCreating && (
        <div className="empty-state">
          <span className="empty-state-icon" aria-hidden="true">
            <Buildings weight="bold" />
          </span>
          <p className="empty-state-title">Todavía no hay empresas</p>
          <button className="btn btn-rosa" onClick={openCreate}>
            Registrar la primera empresa
          </button>
        </div>
      )}

      {companies !== null && companies.length > 0 && (
        <motion.ul className="employee-list" variants={stackTravel} initial="initial" animate="animate">
          {companies.map((company) => {
            const assignable = activeOwners.filter(
              (owner) => !company.owners.some((assigned) => assigned.id === owner.id)
            );

            return (
              <motion.li
                key={company.id}
                variants={rowTravel}
                className={company.is_active ? "employee-row" : "employee-row is-inactive"}
              >
                {editingId === company.id ? (
                  <form className="employee-edit" onSubmit={handleSave}>
                    <CompanyFields idPrefix={"edit-" + company.id} value={editForm} onChange={setEditForm} />
                    <div className="employee-edit-actions">
                      <SubmitButton label="Guardar cambios" loadingLabel="Guardando…" isLoading={isSaving} />
                      <button type="button" className="btn btn-line" onClick={() => setEditingId(null)}>
                        Cancelar
                      </button>
                    </div>
                  </form>
                ) : (
                  <>
                    <div className="employee-row-main">
                      <p className="employee-row-name">
                        {company.legal_name}
                        {!company.is_active && <span className="employee-tag">Inactiva</span>}
                      </p>
                      <p className="employee-row-meta">{companyMeta(company)}</p>
                      <ul className="owner-chips" aria-label={"Dueños de " + company.legal_name}>
                        {company.owners.length === 0 && (
                          <li className="owner-chips-empty">Sin dueño asignado</li>
                        )}
                        {company.owners.map((owner) => (
                          <li key={owner.id} className="owner-chip">
                            {owner.name}
                            {!owner.is_active && " (desactivado)"}
                            <button
                              type="button"
                              onClick={() => handleUnassign(company, owner.id)}
                              disabled={busyId === company.id}
                              aria-label={"Quitar a " + owner.name + " de " + company.legal_name}
                            >
                              <X weight="bold" />
                            </button>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div className="employee-row-actions company-row-actions">
                      {assignable.length > 0 && (
                        <div className="owner-assign">
                          <SelectField
                            id={"assign-" + company.id}
                            label="Sumar dueño"
                            value={ownerToAssign[company.id] ?? ""}
                            onChange={(value) =>
                              setOwnerToAssign((current) => ({ ...current, [company.id]: value }))
                            }
                            options={[
                              { value: "", label: "Elige un dueño" },
                              ...assignable.map((owner) => ({ value: String(owner.id), label: owner.name }))
                            ]}
                          />
                          <button
                            className="btn btn-line"
                            onClick={() => handleAssign(company)}
                            disabled={!ownerToAssign[company.id] || busyId === company.id}
                          >
                            Asignar
                          </button>
                        </div>
                      )}
                      <button className="btn btn-line" onClick={() => startEditing(company)}>
                        Editar
                      </button>
                    </div>
                  </>
                )}
              </motion.li>
            );
          })}
        </motion.ul>
      )}
    </div>
  );
}
