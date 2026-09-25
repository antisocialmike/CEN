import axios from "axios";
import { clearSession, getRole, getToken } from "./authSession";
import { COMPANY_HEADER, getActiveCompanyId } from "./activeCompany";

const httpClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL
});

httpClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  const companyId = getActiveCompanyId();
  if (companyId !== null && getRole() === "admin") {
    config.headers[COMPANY_HEADER] = String(companyId);
  }
  return config;
});

httpClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const isLoginRequest = error.config?.url === "/auth/login";
    if (error.response?.status === 401 && !isLoginRequest) {
      clearSession();
      window.location.replace("/login?sesion=expirada");
    }
    return Promise.reject(error);
  }
);

export default httpClient;
