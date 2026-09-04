import { motion } from "motion/react";

interface SuccessMessageProps {
  message: string;
}

export default function SuccessMessage({ message }: SuccessMessageProps) {
  return (
    <motion.div
      className="success-banner"
      role="status"
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.3 }}
    >
      {message}
    </motion.div>
  );
}
