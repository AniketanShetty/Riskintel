import axios from "axios";

export const apiClient = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
    "X-API-Key": import.meta.env.VITE_API_KEY || "compose-demo-api-key",
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Basic error normalization
    console.error("API Error:", error);
    return Promise.reject(error);
  }
);
