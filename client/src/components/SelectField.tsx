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
}

export default function SelectField({ id, label, value, onChange, options }: SelectFieldProps) {
  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      <div className="form-field-control">
        <select id={id} name={id} value={value} onChange={(event) => onChange(event.target.value)}>
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
