/**
 * Axios-based API client for the VeriCred Share backend.
 * Handles JWT token attachment, response interceptors, and auto-redirect on 401.
 */

import axios, { AxiosError, type AxiosInstance } from "axios";
import type {
  Credential,
  CredentialCreatePayload,
  CredentialListResponse,
  LoginPayload,
  PresentationData,
  RegisterPayload,
  ShareListResponse,
  ShareRequest,
  ShareResponse,
  TokenResponse,
  VerificationResult,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Axios Instance ─────────────────────────────────────
const api: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

// ── Request Interceptor — attach JWT ───────────────────
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ── Response Interceptor — handle 401 ──────────────────
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      // Don't redirect if already on auth pages
      const path = window.location.pathname;
      if (!path.startsWith("/login") && !path.startsWith("/register")) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// ── Auth Endpoints ─────────────────────────────────────
export const authApi = {
  register: (data: RegisterPayload) =>
    api.post<TokenResponse>("/auth/register", data),

  login: (data: LoginPayload) =>
    api.post<TokenResponse>("/auth/login", data),
};

// ── Credential Endpoints ───────────────────────────────
export const credentialApi = {
  issue: (data: CredentialCreatePayload) =>
    api.post<Credential>("/credentials/issue", data),

  list: () => api.get<CredentialListResponse>("/credentials"),

  getById: (id: string) => api.get<Credential>(`/credentials/${id}`),
};

// ── Share Endpoints ────────────────────────────────────
export const shareApi = {
  create: (data: ShareRequest) =>
    api.post<ShareResponse>("/credentials/share", data),

  list: () => api.get<ShareListResponse>("/credentials/shares"),

  revoke: (token: string) =>
    api.delete(`/credentials/shares/${token}`),
};

// ── Verification Endpoints (public, no auth) ───────────
export const verifyApi = {
  getPresentation: (token: string) =>
    axios.get<PresentationData>(`${API_BASE_URL}/api/v1/verify/${token}`),

  verify: (token: string) =>
    axios.post<VerificationResult>(
      `${API_BASE_URL}/api/v1/verify`,
      null,
      { params: { share_token: token } }
    ),
};

export default api;
