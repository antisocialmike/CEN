import { ReactNode, useState } from "react";
import { EyeIcon, EyeOffIcon } from "./icons";

interface FormFieldProps {
  id: string;
  label: string;
  type: string;
  value: string;
  onChange: (value: string) => void;
  autoComplete?: string;
  required?: boolean;
  icon?: ReactNode;
  min?: number;
  step?: number;
}

export default function FormField({
  id,
  label,
  type,
  value,
  onChange,
  autoComplete,
  required,
  icon,
  min,
  step
}: FormFieldProps) {
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);
  const isPasswordField = type === "password";
  const resolvedType = isPasswordField && isPasswordVisible ? "text" : type;

  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      <div className={`form-field-control${icon ? " has-icon" : ""}`}>
        {icon && <span className="form-field-icon">{icon}</span>}
        <input
          id={id}
          name={id}
          type={resolvedType}
          value={value}
          autoComplete={autoComplete}
          required={required}
          min={min}
          step={step}
          onChange={(event) => onChange(event.target.value)}
        />
        {isPasswordField && (
          <button
            type="button"
            className="form-field-toggle"
            onClick={() => setIsPasswordVisible((current) => !current)}
            aria-label={isPasswordVisible ? "Ocultar contraseña" : "Mostrar contraseña"}
          >
            {isPasswordVisible ? <EyeOffIcon /> : <EyeIcon />}
          </button>
        )}
      </div>
    </div>
  );
}
