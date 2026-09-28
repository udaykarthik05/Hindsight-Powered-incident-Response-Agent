import {
  BackendHealth,
  HindsightConnectionStatus,
  Incident,
  IncidentCreate,
  IncidentResolve,
  IncidentResolveResponse,
  IncidentUpdate,
  InvestigationResult,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  try {
    const response = await fetch(url, { ...options, headers });

    if (!response.ok) {
      let errorDetail = `HTTP ${response.status} ${response.statusText}`;
      try {
        const errorJson = await response.json();
        if (errorJson.detail) {
          errorDetail = typeof errorJson.detail === "string"
            ? errorJson.detail
            : JSON.stringify(errorJson.detail);
        }
      } catch {
        // Fallback to status text
      }
      throw new ApiError(errorDetail, response.status);
    }

    return (await response.json()) as T;
  } catch (err: any) {
    if (err instanceof ApiError) {
      throw err;
    }
    // Network / connection refused error
    throw new ApiError(
      `Cannot connect to backend API server at ${API_BASE_URL}. Ensure the FastAPI server is running.`,
      0
    );
  }
}

export const api = {
  // Health & Diagnostics
  getHealth: () => request<BackendHealth>("/health"),
  getHindsightStatus: () => request<HindsightConnectionStatus>("/api/v1/hindsight/status"),

  // Incident Operations
  getIncidents: (filters?: { status?: string; severity?: string; service?: string }) => {
    const params = new URLSearchParams();
    if (filters?.status) params.append("status", filters.status);
    if (filters?.severity) params.append("severity", filters.severity);
    if (filters?.service) params.append("service", filters.service);
    const queryString = params.toString();
    return request<Incident[]>(`/api/v1/incidents${queryString ? `?${queryString}` : ""}`);
  },

  getIncident: (incidentId: string) => request<Incident>(`/api/v1/incidents/${incidentId}`),

  createIncident: (payload: IncidentCreate) =>
    request<Incident>("/api/v1/incidents", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateIncident: (incidentId: string, payload: IncidentUpdate) =>
    request<Incident>(`/api/v1/incidents/${incidentId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  resolveIncident: (incidentId: string, payload: IncidentResolve) =>
    request<IncidentResolveResponse>(`/api/v1/incidents/${incidentId}/resolve`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // AI Investigation Pipeline
  investigateIncident: (incidentId: string) =>
    request<InvestigationResult>(`/api/v1/incidents/${incidentId}/investigate`, {
      method: "POST",
    }),
};
