import { motion } from "motion/react";

interface SubmitButtonProps {
  label: string;
  loadingLabel: string;
  isLoading: boolean;
}

export default function SubmitButton({ label, loadingLabel, isLoading }: SubmitButtonProps) {
  return (
    <motion.button
      className="submit-button"
      type="submit"
      disabled={isLoading}
      whileHover={isLoading ? undefined : { scale: 1.02 }}
      whileTap={isLoading ? undefined : { scale: 0.97 }}
    >
      {isLoading ? (
        <span className="submit-button-loading">
          <span className="submit-button-spinner" />
          {loadingLabel}
        </span>
      ) : (
        label
      )}
    </motion.button>
  );
}
