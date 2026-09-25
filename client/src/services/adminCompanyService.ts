import httpClient from "./httpClient";

export interface AdminCompany {
  id: number;
  legal_name: string;
  trade_name: string | null;
}

export async function listMyCompanies(): Promise<AdminCompany[]> {
  const response = await httpClient.get<AdminCompany[]>("/admin/companies");
  return response.data;
}
