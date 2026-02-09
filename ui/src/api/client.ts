import axios from "axios";

/**
 * Axios instance pointing to the FastAPI backend.
 * In dev, defaults to http://localhost:8000 (the FastAPI server).
 * Override with VITE_API_BASE_URL if needed.
 */
const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

export default client;
