import { motion } from "motion/react";
import { CheckCircle } from "@phosphor-icons/react";

interface SuccessMessageProps {
  message: string;
}

export default function SuccessMessage({ message }: SuccessMessageProps) {
  return (
    <motion.div
      className="success-banner"
      role="status"
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
    >
      <CheckCircle weight="bold" />
      <span>{message}</span>
    </motion.div>
  );
}
