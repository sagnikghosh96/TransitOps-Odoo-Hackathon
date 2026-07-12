import axios from "axios";

// In Codespaces, the backend runs on port 8000. When you forward port 8000,
// set VITE_API_URL to that forwarded URL in a .env file, or leave as-is
// for local dev where both run on localhost.
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("transitops_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("transitops_token");
      localStorage.removeItem("transitops_user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;