import { motion } from "motion/react";
import { WarningCircle } from "@phosphor-icons/react";

interface ErrorMessageProps {
  message: string;
}

export default function ErrorMessage({ message }: ErrorMessageProps) {
  return (
    <motion.div
      className="error-banner"
      role="alert"
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
    >
      <WarningCircle weight="bold" />
      <span>{message}</span>
    </motion.div>
  );
}
