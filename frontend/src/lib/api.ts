import axios from "axios";

const gatewayBaseUrl = import.meta.env.VITE_API_GATEWAY_BASE_URL;

export const authApi = axios.create({
  baseURL: gatewayBaseUrl || import.meta.env.VITE_AUTH_API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

export const procurementApi = axios.create({
  baseURL: gatewayBaseUrl || import.meta.env.VITE_PROCUREMENT_API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

export const inventoryApi = axios.create({
  baseURL: gatewayBaseUrl || import.meta.env.VITE_INVENTORY_API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

function attachAuthInterceptors(instance: typeof authApi) {
  instance.interceptors.request.use((config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  instance.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.removeItem("access_token");
        if (window.location.pathname !== "/login") {
          window.location.href = "/login";
        }
      }
      return Promise.reject(error);
    }
  );
}

attachAuthInterceptors(authApi);
attachAuthInterceptors(inventoryApi);
attachAuthInterceptors(procurementApi);

export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return "Something went wrong. Please try again.";
}