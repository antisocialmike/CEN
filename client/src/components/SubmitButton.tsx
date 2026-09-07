interface SubmitButtonProps {
  label: string;
  loadingLabel: string;
  isLoading: boolean;
}

export default function SubmitButton({ label, loadingLabel, isLoading }: SubmitButtonProps) {
  return (
    <button
      className="btn btn-rosa btn-block"
      type="submit"
      disabled={isLoading}
      aria-busy={isLoading}
    >
      {isLoading && <span className="btn-spinner" aria-hidden="true" />}
      {isLoading ? loadingLabel : label}
    </button>
  );
}
