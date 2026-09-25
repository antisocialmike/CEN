export const ENTIDADES_FEDERATIVAS = [
  { value: "AGU", label: "Aguascalientes" },
  { value: "BCN", label: "Baja California" },
  { value: "BCS", label: "Baja California Sur" },
  { value: "CAM", label: "Campeche" },
  { value: "CHP", label: "Chiapas" },
  { value: "CHH", label: "Chihuahua" },
  { value: "CMX", label: "Ciudad de México" },
  { value: "COA", label: "Coahuila" },
  { value: "COL", label: "Colima" },
  { value: "DUR", label: "Durango" },
  { value: "GUA", label: "Guanajuato" },
  { value: "GRO", label: "Guerrero" },
  { value: "HID", label: "Hidalgo" },
  { value: "JAL", label: "Jalisco" },
  { value: "MEX", label: "Estado de México" },
  { value: "MIC", label: "Michoacán" },
  { value: "MOR", label: "Morelos" },
  { value: "NAY", label: "Nayarit" },
  { value: "NLE", label: "Nuevo León" },
  { value: "OAX", label: "Oaxaca" },
  { value: "PUE", label: "Puebla" },
  { value: "QUE", label: "Querétaro" },
  { value: "ROO", label: "Quintana Roo" },
  { value: "SLP", label: "San Luis Potosí" },
  { value: "SIN", label: "Sinaloa" },
  { value: "SON", label: "Sonora" },
  { value: "TAB", label: "Tabasco" },
  { value: "TAM", label: "Tamaulipas" },
  { value: "TLA", label: "Tlaxcala" },
  { value: "VER", label: "Veracruz" },
  { value: "YUC", label: "Yucatán" },
  { value: "ZAC", label: "Zacatecas" }
] as const;

export type EntidadFederativa = (typeof ENTIDADES_FEDERATIVAS)[number]["value"];

export interface CompanyInput {
  legalName: string;
  tradeName: string;
  rfc: string;
  registroPatronal: string;
  entidadFederativa: EntidadFederativa | "";
}

export function companyPayload(input: CompanyInput) {
  return {
    legal_name: input.legalName,
    trade_name: input.tradeName || null,
    rfc: input.rfc || null,
    registro_patronal: input.registroPatronal || null,
    entidad_federativa: input.entidadFederativa || null
  };
}

export interface CompanyDataFields {
  legal_name: string;
  trade_name: string | null;
  rfc: string | null;
  registro_patronal: string | null;
  entidad_federativa: EntidadFederativa | null;
}

export function entidadLabel(value: EntidadFederativa | null): string | null {
  return ENTIDADES_FEDERATIVAS.find((entidad) => entidad.value === value)?.label ?? null;
}

export function companyMeta(company: CompanyDataFields): string {
  const parts = [
    company.trade_name,
    company.rfc ? "RFC " + company.rfc : "Sin RFC",
    entidadLabel(company.entidad_federativa)
  ];
  return parts.filter(Boolean).join(" · ");
}

export function toCompanyInput(company: CompanyDataFields): CompanyInput {
  return {
    legalName: company.legal_name,
    tradeName: company.trade_name ?? "",
    rfc: company.rfc ?? "",
    registroPatronal: company.registro_patronal ?? "",
    entidadFederativa: company.entidad_federativa ?? ""
  };
}
