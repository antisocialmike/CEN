import httpClient from "./httpClient";
import { companyPayload, CompanyInput, EntidadFederativa } from "./companyData";
import { Pagina, POR_PAGINA } from "./pagina";

export { ENTIDADES_FEDERATIVAS } from "./companyData";
export type { CompanyInput, EntidadFederativa } from "./companyData";

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

export async function listOwners(): Promise<Owner[]> {
  const response = await httpClient.get<Owner[]>("/superadmin/owners");
  return response.data;
}

export async function listOwnersPage(pagina: number): Promise<Pagina<Owner>> {
  const response = await httpClient.get<Pagina<Owner>>("/superadmin/owners", {
    params: { page: pagina, page_size: POR_PAGINA }
  });
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

export async function listCompaniesPage(pagina: number): Promise<Pagina<Company>> {
  const response = await httpClient.get<Pagina<Company>>("/superadmin/companies", {
    params: { page: pagina, page_size: POR_PAGINA }
  });
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
