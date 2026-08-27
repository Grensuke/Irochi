/**
 * API service — HTTP client for the FastAPI backend.
 *
 * DUMMY PHASE: Calls the existing dummy endpoints.
 * FUTURE: Same interface, real backend responses.
 *
 * The Vite dev server proxies /api → http://localhost:8000.
 */

import type { AlertListResponse, DashboardSummary, HealthResponse, Alert } from '../types';

const API_BASE = '/api/v1';

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
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

  /** GET /api/v1/dashboard/summary */
  getDashboardSummary(): Promise<DashboardSummary> {
    return fetchJson<DashboardSummary>('/dashboard/summary');
  },
};
