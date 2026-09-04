import { motion } from "motion/react";

interface ErrorMessageProps {
  message: string;
}

export default function ErrorMessage({ message }: ErrorMessageProps) {
  return (
    <motion.div
      className="error-banner"
      role="alert"
      initial={{ opacity: 0, x: 0 }}
      animate={{ opacity: 1, x: [0, -8, 8, -6, 6, 0] }}
      transition={{ duration: 0.4 }}
    >
      {message}
    </motion.div>
  );
}
