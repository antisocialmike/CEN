interface LoadingSpinnerProps {
  label: string;
}

export default function LoadingSpinner({ label }: LoadingSpinnerProps) {
  return <p className="loading-text">{label}</p>;
}
