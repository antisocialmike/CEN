import { motion } from "motion/react";
import { LogoMark } from "./icons";

export default function AppLoader() {
  return (
    <motion.div
      className="app-loader"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.25 }}
    >
      <div className="app-loader-mark">
        <LogoMark />
        <motion.span
          className="app-loader-ring"
          animate={{ rotate: 360 }}
          transition={{ duration: 0.9, repeat: Infinity, ease: "linear" }}
        />
      </div>
      <motion.p
        className="app-loader-brand"
        animate={{ opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
      >
        CEN Payroll
      </motion.p>
    </motion.div>
  );
}
