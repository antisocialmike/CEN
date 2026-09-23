import httpClient from "./httpClient";

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

export interface CompanySummary {
  id: number;
  legal_name: string;
  is_active: boolean;
}

export interface OwnerSummary {
  id: number;
  name: string;
  is_active: boolean;
}

export interface Owner {
  id: number;
  name: string;
  email: string;
  is_active: boolean;
  companies: CompanySummary[];
}

export interface OwnerInput {
  name: string;
  email: string;
}

export interface OwnerCreated {
  owner: Owner;
  temporary_password: string;
}

export interface OwnerPasswordReset {
  owner_id: number;
  name: string;
  email: string;
  temporary_password: string;
}

export interface Company {
  id: number;
  legal_name: string;
  trade_name: string | null;
  rfc: string | null;
  registro_patronal: string | null;
  entidad_federativa: EntidadFederativa | null;
  is_active: boolean;
  created_at: string;
  owners: OwnerSummary[];
}

export interface CompanyInput {
  legalName: string;
  tradeName: string;
  rfc: string;
  registroPatronal: string;
  entidadFederativa: EntidadFederativa | "";
}

function companyPayload(input: CompanyInput) {
  return {
    legal_name: input.legalName,
    trade_name: input.tradeName || null,
    rfc: input.rfc || null,
    registro_patronal: input.registroPatronal || null,
    entidad_federativa: input.entidadFederativa || null
  };
}

export async function listOwners(): Promise<Owner[]> {
  const response = await httpClient.get<Owner[]>("/superadmin/owners");
  return response.data;
}

export async function createOwner(input: OwnerInput): Promise<OwnerCreated> {
  const response = await httpClient.post<OwnerCreated>("/superadmin/owners", input);
  return response.data;
}

export async function updateOwner(id: number, input: OwnerInput): Promise<Owner> {
  const response = await httpClient.put<Owner>(`/superadmin/owners/${id}`, input);
  return response.data;
}

export async function setOwnerActive(id: number, isActive: boolean): Promise<Owner> {
  const action = isActive ? "activate" : "deactivate";
  const response = await httpClient.post<Owner>(`/superadmin/owners/${id}/${action}`);
  return response.data;
}

export async function resetOwnerPassword(id: number): Promise<OwnerPasswordReset> {
  const response = await httpClient.post<OwnerPasswordReset>(
    `/superadmin/owners/${id}/reset-password`
  );
  return response.data;
}

export async function listCompanies(): Promise<Company[]> {
  const response = await httpClient.get<Company[]>("/superadmin/companies");
  return response.data;
}

export async function createCompany(input: CompanyInput, ownerId: number): Promise<Company> {
  const response = await httpClient.post<Company>("/superadmin/companies", {
    ...companyPayload(input),
    owner_id: ownerId
  });
  return response.data;
}

export async function updateCompany(id: number, input: CompanyInput): Promise<Company> {
  const response = await httpClient.put<Company>(
    `/superadmin/companies/${id}`,
    companyPayload(input)
  );
  return response.data;
}

export async function assignCompanyOwner(companyId: number, ownerId: number): Promise<Company> {
  const response = await httpClient.post<Company>(`/superadmin/companies/${companyId}/owners`, {
    owner_id: ownerId
  });
  return response.data;
}

export async function unassignCompanyOwner(companyId: number, ownerId: number): Promise<Company> {
  const response = await httpClient.delete<Company>(
    `/superadmin/companies/${companyId}/owners/${ownerId}`
  );
  return response.data;
}
