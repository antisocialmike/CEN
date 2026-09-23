import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import { Buildings, EnvelopeSimple, UserCirclePlus, UsersThree } from "@phosphor-icons/react";
import { rowVariants, stackVariants, useStill } from "../motion/variants";
import FormField from "../components/FormField";
import ErrorMessage from "../components/ErrorMessage";
import SuccessMessage from "../components/SuccessMessage";
import SubmitButton from "../components/SubmitButton";
import Skeleton from "../components/Skeleton";
import TemporaryPassword from "../components/TemporaryPassword";
import {
  createOwner,
  listOwners,
  Owner,
  OwnerInput,
  resetOwnerPassword,
  setOwnerActive,
  updateOwner
} from "../services/superadminService";
import { getErrorDetail, getStatusCode } from "../services/apiError";

type Confirming = { id: number; action: "reset" | "toggle" } | null;

interface IssuedPassword {
  name: string;
  password: string;
}

const emptyForm: OwnerInput = { name: "", email: "" };

function companiesLabel(owner: Owner): string {
  if (owner.companies.length === 0) return "Sin empresas asignadas";
  return owner.companies.map((company) => company.legal_name).join(", ");
}

export default function SuperadminOwnersPage() {
  const stackTravel = useStill(stackVariants);
  const rowTravel = useStill(rowVariants);
  const navigate = useNavigate();
  const [owners, setOwners] = useState<Owner[] | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newOwner, setNewOwner] = useState<OwnerInput>(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<OwnerInput>(emptyForm);
  const [confirming, setConfirming] = useState<Confirming>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [issuedPassword, setIssuedPassword] = useState<IssuedPassword | null>(null);

  useEffect(() => {
    let isMounted = true;

    listOwners()
      .then((result) => isMounted && setOwners(result))
      .catch(() => {
        if (!isMounted) return;
        setOwners([]);
        setErrorMessage("No se pudo cargar la lista de dueños. Recarga la página.");
      });

    return () => {
      isMounted = false;
    };
  }, []);

  function clearMessages() {
    setErrorMessage(null);
    setSuccessMessage(null);
  }

  function replaceOwner(updated: Owner) {
    setOwners((current) =>
      (current ?? []).map((item) => (item.id === updated.id ? updated : item))
    );
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    clearMessages();
    setIsSaving(true);

    try {
      const created = await createOwner(newOwner);
      setOwners((current) => [created.owner, ...(current ?? [])]);
      setIssuedPassword({ name: created.owner.name, password: created.temporary_password });
      setNewOwner(emptyForm);
      setIsCreating(false);
    } catch (error) {
      setErrorMessage(
        getStatusCode(error) === 409
          ? "Ese correo ya está registrado. Usa otro."
          : "No se pudo dar de alta al dueño. Revisa los datos e inténtalo de nuevo."
      );
    } finally {
      setIsSaving(false);
    }
  }

  function startEditing(owner: Owner) {
    clearMessages();
    setConfirming(null);
    setEditingId(owner.id);
    setEditForm({ name: owner.name, email: owner.email });
  }

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (editingId === null) return;
    clearMessages();
    setIsSaving(true);

    try {
      const updated = await updateOwner(editingId, editForm);
      replaceOwner(updated);
      setSuccessMessage("Se guardaron los cambios de " + updated.name + ".");
      setEditingId(null);
    } catch (error) {
      const status = getStatusCode(error);
      setErrorMessage(
        status === 409
          ? "Ese correo ya lo usa otra persona. Elige uno distinto."
          : status === 404
            ? "Ese dueño ya no existe. Recarga la página."
            : "No se pudieron guardar los cambios. Inténtalo de nuevo."
      );
    } finally {
      setIsSaving(false);
    }
  }

  function ask(owner: Owner, action: "reset" | "toggle") {
    clearMessages();
    setEditingId(null);
    setConfirming({ id: owner.id, action });
  }

  async function confirmReset(owner: Owner) {
    clearMessages();
    setBusyId(owner.id);

    try {
      const reset = await resetOwnerPassword(owner.id);
      setIssuedPassword({ name: reset.name, password: reset.temporary_password });
    } catch {
      setErrorMessage("No se pudo restablecer la contraseña. Inténtalo de nuevo.");
    } finally {
      setBusyId(null);
      setConfirming(null);
    }
  }

  async function confirmToggle(owner: Owner) {
    clearMessages();
    setBusyId(owner.id);

    try {
      const updated = await setOwnerActive(owner.id, !owner.is_active);
      replaceOwner(updated);
      setSuccessMessage(
        updated.is_active
          ? updated.name + " puede volver a entrar."
          : updated.name + " ya no puede entrar. Sus empresas se conservan."
      );
    } catch (error) {
      setErrorMessage(
        getStatusCode(error) === 409
          ? (getErrorDetail(error) ?? "Alguna de sus empresas se quedaría sin dueño activo.") +
              ". Asígnales otro dueño antes de desactivarlo."
          : "No se pudo cambiar el estado. Inténtalo de nuevo."
      );
    } finally {
      setBusyId(null);
      setConfirming(null);
    }
  }

  return (
    <div className="dashboard-panel">
      <div className="dashboard-panel-header">
        <div className="dashboard-panel-heading">
          <span className="panel-icon-badge" aria-hidden="true">
            <UsersThree weight="bold" />
          </span>
          <div>
            <h1>Dueños</h1>
            <p className="dashboard-panel-subtitle">
              Da de alta a los dueños de las empresas. Cada uno entra con una contraseña temporal
              y la cambia en su primer acceso.
            </p>
          </div>
        </div>
        <div className="dashboard-panel-actions">
          <button className="btn btn-line" onClick={() => navigate("/superadmin/empresas")}>
            <Buildings weight="bold" />
            Empresas
          </button>
          {!isCreating && (
            <button
              className="btn btn-rosa"
              onClick={() => {
                clearMessages();
                setIsCreating(true);
              }}
            >
              <UserCirclePlus weight="bold" />
              Nuevo dueño
            </button>
          )}
        </div>
      </div>

      <AnimatePresence mode="wait">
        {errorMessage && <ErrorMessage key="error" message={errorMessage} />}
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

      {isCreating && (
        <form className="employee-edit" onSubmit={handleCreate} aria-label="Nuevo dueño">
          <FormField
            id="owner-name"
            label="Nombre completo"
            type="text"
            value={newOwner.name}
            onChange={(value) => setNewOwner({ ...newOwner, name: value })}
            autoComplete="off"
            placeholder="Laura Méndez"
            icon={<UsersThree weight="bold" />}
            required
          />
          <FormField
            id="owner-email"
            label="Correo"
            type="email"
            value={newOwner.email}
            onChange={(value) => setNewOwner({ ...newOwner, email: value })}
            autoComplete="off"
            inputMode="email"
            placeholder="nombre@empresa.mx"
            icon={<EnvelopeSimple weight="bold" />}
            hint="Será su usuario. La contraseña temporal se genera al guardar."
            required
          />
          <div className="employee-edit-actions">
            <SubmitButton label="Dar de alta" loadingLabel="Guardando…" isLoading={isSaving} />
            <button type="button" className="btn btn-line" onClick={() => setIsCreating(false)}>
              Cancelar
            </button>
          </div>
        </form>
      )}

      {owners === null && (
        <div className="skeleton-stack" aria-hidden="true">
          <Skeleton height={64} />
          <Skeleton height={64} />
          <Skeleton height={64} />
        </div>
      )}

      {owners !== null && owners.length === 0 && !isCreating && (
        <div className="empty-state">
          <span className="empty-state-icon" aria-hidden="true">
            <UsersThree weight="bold" />
          </span>
          <p className="empty-state-title">Todavía no hay dueños</p>
          <button className="btn btn-rosa" onClick={() => setIsCreating(true)}>
            Dar de alta al primer dueño
          </button>
        </div>
      )}

      {owners !== null && owners.length > 0 && (
        <motion.ul className="employee-list" variants={stackTravel} initial="initial" animate="animate">
          {owners.map((owner) => (
            <motion.li
              key={owner.id}
              variants={rowTravel}
              className={owner.is_active ? "employee-row" : "employee-row is-inactive"}
            >
              {editingId === owner.id ? (
                <form className="employee-edit" onSubmit={handleSave}>
                  <FormField
                    id={"name-" + owner.id}
                    label="Nombre completo"
                    type="text"
                    value={editForm.name}
                    onChange={(value) => setEditForm({ ...editForm, name: value })}
                    required
                  />
                  <FormField
                    id={"email-" + owner.id}
                    label="Correo"
                    type="email"
                    value={editForm.email}
                    onChange={(value) => setEditForm({ ...editForm, email: value })}
                    inputMode="email"
                    required
                  />
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
                      {owner.name}
                      {!owner.is_active && <span className="employee-tag">Desactivado</span>}
                    </p>
                    <p className="employee-row-meta">
                      {owner.email} · {companiesLabel(owner)}
                    </p>
                  </div>
                  {confirming?.id === owner.id ? (
                    <div className="employee-row-confirm">
                      <p>
                        {confirming.action === "reset"
                          ? "La contraseña actual de " + owner.name + " dejará de funcionar."
                          : owner.is_active
                            ? owner.name + " ya no podrá entrar."
                            : owner.name + " podrá volver a entrar."}
                      </p>
                      <div className="employee-row-actions">
                        <button
                          className="btn btn-rosa"
                          onClick={() =>
                            confirming.action === "reset" ? confirmReset(owner) : confirmToggle(owner)
                          }
                          disabled={busyId === owner.id}
                        >
                          {busyId === owner.id
                            ? "Procesando…"
                            : confirming.action === "reset"
                              ? "Restablecer"
                              : owner.is_active
                                ? "Desactivar"
                                : "Reactivar"}
                        </button>
                        <button
                          className="btn btn-line"
                          onClick={() => setConfirming(null)}
                          disabled={busyId === owner.id}
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="employee-row-actions">
                      <button className="btn btn-line" onClick={() => startEditing(owner)}>
                        Editar
                      </button>
                      <button className="btn btn-line" onClick={() => ask(owner, "reset")}>
                        Restablecer contraseña
                      </button>
                      <button className="btn btn-line" onClick={() => ask(owner, "toggle")}>
                        {owner.is_active ? "Desactivar" : "Reactivar"}
                      </button>
                    </div>
                  )}
                </>
              )}
            </motion.li>
          ))}
        </motion.ul>
      )}
    </div>
  );
}
