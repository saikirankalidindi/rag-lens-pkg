/**
 * Typed API client for the RAGLens backend.
 * All fetch calls go through here to centralise base URL and error handling.
 */
import type {
  PaginatedResponse,
  Project,
  ProjectStats,
  Trace,
  TraceListItem,
  ApiKey,
} from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── HTTP helpers ──────────────────────────────────────────────────────────────

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!res.ok) {
    let message = `Request failed (HTTP ${res.status})`;
    try {
      const body = await res.json();
      const detail = body.detail;
      message = body.error?.message ?? (typeof detail === "string" ? detail : detail?.message) ??
        (Array.isArray(detail) ? detail.map((item: { msg: string }) => item.msg).join("; ") : message);
    } catch { /* Keep the HTTP status for non-JSON errors. */ }
    throw new Error(message);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// Token is stored in memory (set after login). For SSR/RSC, pass via headers.
let _token: string | null = null;

export function setAuthToken(token: string | null) {
  _token = token;
}

function authHeaders(): Record<string, string> {
  return _token ? { Authorization: `Bearer ${_token}` } : {};
}

// ── Health ────────────────────────────────────────────────────────────────────

export const healthApi = {
  check: () => request<{ status: string; version: string }>("/health"),
};

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
}

export const authApi = {
  register: (data: RegisterRequest) =>
    request<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (data: LoginRequest) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  me: () =>
    request<User>("/auth/me", {
      headers: authHeaders(),
    }),
};

// ── Projects ──────────────────────────────────────────────────────────────────

export const projectsApi = {
  list: () =>
    request<Project[]>("/projects", { headers: authHeaders() }),

  get: (id: string) =>
    request<Project>(`/projects/${id}`, { headers: authHeaders() }),

  update: (id: string, data: { name: string; description?: string }) =>
    request<Project>(`/projects/${id}`, { method: "PATCH", body: JSON.stringify(data), headers: authHeaders() }),

  getStats: (id: string) =>
    request<ProjectStats>(`/projects/${id}/stats`, { headers: authHeaders() }),

  create: (data: { name: string; description?: string }) =>
    request<Project>("/projects", {
      method: "POST",
      body: JSON.stringify(data),
      headers: authHeaders(),
    }),
};

// ── Traces ────────────────────────────────────────────────────────────────────

export interface TraceFilters {
  started_after?: string;
  started_before?: string;
  sort?: string;
  page?: number;
  page_size?: number;
  status?: string;
  search?: string;
  environment?: string;
}

export const tracesApi = {
  list: (projectId: string, filters: TraceFilters = {}) => {
    const params = new URLSearchParams();
    if (filters.started_after) params.set("started_after", filters.started_after);
    if (filters.started_before) params.set("started_before", filters.started_before);
    if (filters.sort) params.set("sort", filters.sort);
    if (filters.page) params.set("page", String(filters.page));
    if (filters.page_size) params.set("page_size", String(filters.page_size));
    if (filters.status) params.set("status", filters.status);
    if (filters.search) params.set("search", filters.search);
    if (filters.environment) params.set("environment", filters.environment);
    const qs = params.toString();
    return request<PaginatedResponse<TraceListItem>>(
      `/projects/${projectId}/traces${qs ? `?${qs}` : ""}`,
      { headers: authHeaders() }
    );
  },

  get: (projectId: string, traceId: string) =>
    request<Trace>(`/projects/${projectId}/traces/${traceId}`, {
      headers: authHeaders(),
    }),
};

// ── API Keys ──────────────────────────────────────────────────────────────────

export const apiKeysApi = {
  list: (projectId: string) =>
    request<ApiKey[]>(`/projects/${projectId}/api-keys`, {
      headers: authHeaders(),
    }),

  create: (projectId: string, name: string) =>
    request<{ api_key: ApiKey; raw_key: string }>(
      `/projects/${projectId}/api-keys`,
      {
        method: "POST",
        body: JSON.stringify({ name }),
        headers: authHeaders(),
      }
    ),

  revoke: (projectId: string, keyId: string) =>
    request<void>(`/projects/${projectId}/api-keys/${keyId}`, {
      method: "DELETE",
      headers: authHeaders(),
    }),
};
