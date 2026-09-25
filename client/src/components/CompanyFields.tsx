import FormField from "./FormField";
import SelectField from "./SelectField";
import {
  CompanyInput,
  ENTIDADES_FEDERATIVAS,
  EntidadFederativa
} from "../services/companyData";

const ENTIDAD_OPTIONS = [
  { value: "", label: "Sin definir" },
  ...ENTIDADES_FEDERATIVAS.map((entidad) => ({ value: entidad.value, label: entidad.label }))
];

interface CompanyFieldsProps {
  idPrefix: string;
  value: CompanyInput;
  onChange: (value: CompanyInput) => void;
}

export default function CompanyFields({ idPrefix, value, onChange }: CompanyFieldsProps) {
  return (
    <>
      <FormField
        id={idPrefix + "-legal-name"}
        label="Razón social"
        type="text"
        value={value.legalName}
        onChange={(legalName) => onChange({ ...value, legalName })}
        placeholder="Grupo Norte SA de CV"
        maxLength={200}
        required
      />
      <FormField
        id={idPrefix + "-trade-name"}
        label="Nombre comercial"
        type="text"
        value={value.tradeName}
        onChange={(tradeName) => onChange({ ...value, tradeName })}
        maxLength={150}
      />
      <FormField
        id={idPrefix + "-rfc"}
        label="RFC"
        type="text"
        value={value.rfc}
        onChange={(rfc) => onChange({ ...value, rfc: rfc.toUpperCase() })}
        maxLength={13}
        hint="Opcional por ahora. 12 caracteres para persona moral, 13 para física."
      />
      <FormField
        id={idPrefix + "-registro-patronal"}
        label="Registro patronal IMSS"
        type="text"
        value={value.registroPatronal}
        onChange={(registroPatronal) =>
          onChange({ ...value, registroPatronal: registroPatronal.toUpperCase() })
        }
        maxLength={11}
      />
      <SelectField
        id={idPrefix + "-entidad"}
        label="Estado"
        value={value.entidadFederativa}
        onChange={(entidad) =>
          onChange({ ...value, entidadFederativa: entidad as EntidadFederativa | "" })
        }
        options={ENTIDAD_OPTIONS}
        hint="Define el impuesto estatal sobre nómina."
      />
    </>
  );
}
