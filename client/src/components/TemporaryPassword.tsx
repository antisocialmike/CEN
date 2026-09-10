import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { Check, Copy } from "@phosphor-icons/react";

interface TemporaryPasswordProps {
  name: string;
  password: string;
  onDismiss: () => void;
}

type CopyState = "idle" | "copied" | "failed";

export default function TemporaryPassword({ name, password, onDismiss }: TemporaryPasswordProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const [copyState, setCopyState] = useState<CopyState>("idle");
  const shift = useReducedMotion() ? 0 : -6;

  useEffect(() => {
    panelRef.current?.focus();
  }, []);

  async function copyPassword() {
    try {
      await navigator.clipboard.writeText(password);
      setCopyState("copied");
    } catch {
      setCopyState("failed");
    }
  }

  return (
    <motion.div
      ref={panelRef}
      className="temp-password"
      role="region"
      aria-label={"Contraseña temporal de " + name}
      tabIndex={-1}
      initial={{ opacity: 0, y: shift }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: shift }}
      transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
    >
      <p className="temp-password-title">Contraseña temporal de {name}</p>
      <div className="temp-password-row">
        <code className="temp-password-value">{password}</code>
        <button type="button" className="btn btn-ink" onClick={copyPassword}>
          {copyState === "copied" ? <Check weight="bold" /> : <Copy weight="bold" />}
          {copyState === "copied" ? "Copiada" : "Copiar"}
        </button>
      </div>
      <p className="temp-password-note" aria-live="polite">
        {copyState === "failed"
          ? "No se pudo copiar. Selecciónala y cópiala a mano."
          : "Compártela por un canal seguro. No se volverá a mostrar y se le pedirá cambiarla al entrar."}
      </p>
      <button type="button" className="text-button" onClick={onDismiss}>
        Ya la compartí
      </button>
    </motion.div>
  );
}
