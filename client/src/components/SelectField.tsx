interface SelectOption {
  value: string;
  label: string;
}

interface SelectFieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  hint?: string;
}

export default function SelectField({
  id,
  label,
  value,
  onChange,
  options,
  hint
}: SelectFieldProps) {
  const hintId = hint ? `${id}-hint` : undefined;

  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      <div className="form-field-control">
        <select
          id={id}
          name={id}
          value={value}
          aria-describedby={hintId}
          onChange={(event) => onChange(event.target.value)}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      {hint && (
        <p className="form-field-hint" id={hintId}>
          {hint}
        </p>
      )}
    </div>
  );
}
