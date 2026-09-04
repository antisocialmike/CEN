import axios from "axios";
import { clearSession, getToken } from "./authSession";

const httpClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL
});

httpClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

httpClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearSession();
      window.location.replace("/login?sesion=expirada");
    }
    return Promise.reject(error);
  }
);

export default httpClient;
