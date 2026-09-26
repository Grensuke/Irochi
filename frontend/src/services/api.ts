/**
 * API service — HTTP client for the FastAPI backend.
 *
 * DUMMY PHASE: Calls the existing dummy endpoints.
 * FUTURE: Same interface, real backend responses.
 *
 * The Vite dev server proxies /api → http://localhost:8000.
 */

import type { AlertListResponse, DashboardSummary, HealthResponse, Alert, Incident, IncidentListResponse } from '../types';

// Use VITE_API_BASE_URL for Vercel, but fallback to relative path for Vite local proxy
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '') + '/api/v1';

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const err = new Error(`${res.status} ${res.statusText}`);
    err.name = 'ApiError';
    throw err;
  }
  return res.json() as Promise<T>;
}

async function postJson<T>(path: string, body: any): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  });
  if (!res.ok) {
    const err = new Error(`${res.status} ${res.statusText}`);
    err.name = 'ApiError';
    throw err;
  }
  return res.json() as Promise<T>;
}

/** Service layer for REST API calls. */
export const api = {
  /** GET /api/v1/health */
  health(): Promise<HealthResponse> {
    return fetchJson<HealthResponse>('/health');
  },

  /** GET /api/v1/alerts */
  getAlerts(): Promise<AlertListResponse> {
    return fetchJson<AlertListResponse>('/alerts');
  },

  /** GET /api/v1/alerts/{alert_id} */
  getAlert(alertId: string): Promise<Alert> {
    return fetchJson<Alert>(`/alerts/${encodeURIComponent(alertId)}`);
  },

  /** GET /api/v1/incidents */
  getIncidents(status?: string): Promise<IncidentListResponse> {
    const qs = status ? `?status=${encodeURIComponent(status)}` : '';
    return fetchJson<IncidentListResponse>(`/incidents${qs}`);
  },

  /** GET /api/v1/incidents/{incident_id} */
  getIncident(incidentId: string): Promise<Incident> {
    return fetchJson<Incident>(`/incidents/${encodeURIComponent(incidentId)}`);
  },

  /** GET /api/v1/dashboard/summary */
  getDashboardSummary(): Promise<DashboardSummary> {
    return fetchJson<DashboardSummary>('/dashboard/summary');
  },

  /** POST /api/v1/narrative/generate */
  generateNarrative(context: any): Promise<{ what_was_observed: string, why_it_matters: string, what_to_investigate: string }> {
    return postJson('/narrative/generate', context);
  },

  /** POST /api/v1/incidents/{incident_id}/close */
  closeIncident(incidentId: string, payload: { resolution_note?: string; closed_by?: string }): Promise<Incident> {
    return postJson<Incident>(`/incidents/${encodeURIComponent(incidentId)}/close`, payload);
  },
};
