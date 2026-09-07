import { motion, useReducedMotion } from "motion/react";
import { LogoMark } from "./icons";

export default function AppLoader() {
  const reduceMotion = useReducedMotion();

  return (
    <div className="app-loader" role="status" aria-live="polite">
      <div className="app-loader-mark">
        <LogoMark />
        {!reduceMotion && (
          <motion.span
            className="app-loader-ring"
            animate={{ rotate: 360 }}
            transition={{ duration: 0.9, repeat: Infinity, ease: "linear" }}
          />
        )}
      </div>
      <p className="app-loader-brand">Cargando CEN Payroll…</p>
    </div>
  );
}
