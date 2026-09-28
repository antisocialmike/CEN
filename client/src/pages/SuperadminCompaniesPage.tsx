import { FormEvent, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import { Buildings, Plus, UsersThree, X } from "@phosphor-icons/react";
import { rowVariants, stackVariants, useStill } from "../motion/variants";
import SelectField from "../components/SelectField";
import ErrorMessage from "../components/ErrorMessage";
import SuccessMessage from "../components/SuccessMessage";
import SubmitButton from "../components/SubmitButton";
import Skeleton from "../components/Skeleton";
import CompanyFields from "../components/CompanyFields";
import Paginacion from "../components/Paginacion";
import { useListaPaginada } from "../routes/listaPaginada";
import { companyMeta, toCompanyInput } from "../services/companyData";
import {
  assignCompanyOwner,
  Company,
  CompanyInput,
  createCompany,
  listCompaniesPage,
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

function saveErrorMessage(error: unknown): string {
  const status = getStatusCode(error);
  if (status === 409) return "Ese RFC ya pertenece a otra empresa.";
  if (status === 422) return "Revisa el RFC (12 o 13 caracteres) y el registro patronal (letra y 10 dígitos).";
  if (status === 404) return "El dueño elegido ya no está activo. Recarga la página.";
  return "No se pudieron guardar los datos de la empresa. Inténtalo de nuevo.";
}

export default function SuperadminCompaniesPage() {
  const stackTravel = useStill(stackVariants);
  const rowTravel = useStill(rowVariants);
  const navigate = useNavigate();
  const lista = useListaPaginada(listCompaniesPage);
  const companies = lista.items;
  const inicioDeLista = useRef<HTMLUListElement>(null);
  // Los duenos van completos: alimentan los selectores de asignar, no se paginan.
  const [owners, setOwners] = useState<Owner[]>([]);
  const [ownersFailed, setOwnersFailed] = useState(false);
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
  // Los fallos al cargar no se borran al intentar otra accion: los datos siguen sin llegar.
  const shownError =
    errorMessage ??
    (lista.fallo
      ? "No se pudo cargar la lista de empresas. Recarga la página."
      : ownersFailed
        ? "No se pudo cargar la lista de dueños para asignar. Recarga la página."
        : null);

  useEffect(() => {
    let isMounted = true;

    listOwners()
      .then((ownerList) => isMounted && setOwners(ownerList))
      .catch(() => isMounted && setOwnersFailed(true));

    return () => {
      isMounted = false;
    };
  }, []);

  function clearMessages() {
    setErrorMessage(null);
    setSuccessMessage(null);
  }

  function replaceCompany(updated: Company) {
    lista.actualizar((current) =>
      current.map((item) => (item.id === updated.id ? updated : item))
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
      // Queda en el lugar que le toca por nombre, que puede ser otra pagina.
      lista.recargar();
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
    setEditForm(toCompanyInput(company));
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
        {shownError && <ErrorMessage key="error" message={shownError} />}
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
        <motion.ul
          ref={inicioDeLista}
          className="employee-list"
          variants={stackTravel}
          initial="initial"
          animate="animate"
        >
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

      <Paginacion
        pagina={lista.pagina}
        total={lista.total}
        porPagina={lista.porPagina}
        etiqueta="Páginas de empresas"
        alCambiar={lista.irAPagina}
        destino={inicioDeLista}
      />
    </div>
  );
}
