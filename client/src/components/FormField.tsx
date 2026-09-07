import { ReactNode, useState } from "react";
import { Eye, EyeSlash } from "@phosphor-icons/react";

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
  placeholder?: string;
  hint?: string;
  prefix?: string;
  inputMode?: "text" | "numeric" | "decimal" | "email";
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
  step,
  placeholder,
  hint,
  prefix,
  inputMode
}: FormFieldProps) {
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);
  const isPasswordField = type === "password";
  const resolvedType = isPasswordField && isPasswordVisible ? "text" : type;
  const hintId = hint ? `${id}-hint` : undefined;

  const controlClass = [
    "form-field-control",
    icon ? "has-icon" : "",
    prefix ? "has-prefix" : "",
    isPasswordField ? "has-toggle" : ""
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      <div className={controlClass}>
        {icon && <span className="form-field-icon">{icon}</span>}
        {prefix && <span className="form-field-prefix">{prefix}</span>}
        <input
          id={id}
          name={id}
          type={resolvedType}
          value={value}
          autoComplete={autoComplete}
          required={required}
          min={min}
          step={step}
          placeholder={placeholder}
          inputMode={inputMode}
          aria-describedby={hintId}
          onChange={(event) => onChange(event.target.value)}
        />
        {isPasswordField && (
          <button
            type="button"
            className="form-field-toggle"
            onClick={() => setIsPasswordVisible((current) => !current)}
            aria-label={isPasswordVisible ? "Ocultar contraseña" : "Mostrar contraseña"}
            aria-pressed={isPasswordVisible}
          >
            {isPasswordVisible ? <EyeSlash weight="bold" /> : <Eye weight="bold" />}
          </button>
        )}
      </div>
      {hint && (
        <p className="form-field-hint" id={hintId}>
          {hint}
        </p>
      )}
    </div>
  );
}
