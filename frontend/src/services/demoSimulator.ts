import { api } from './api';
import type { Alert, DashboardSummary } from '../types';

// Store references to the original API methods so we can restore them when the demo stops
const originalGetAlerts = api.getAlerts;
const originalGetDashboardSummary = api.getDashboardSummary;

let isRunning = false;
let demoAlerts: Alert[] = [];
let rawAlertTemplates: any[] = [];
let currentIndex = 0;
let loopInterval: ReturnType<typeof setInterval> | null = null;

// The backend sends 50 backfill alerts when WS connects, so we start the simulation 
// with a clean slate (0 alerts) to satisfy the user's request, and let it build up.
export const demoSimulator = {
  start: async () => {
    if (isRunning) return;
    isRunning = true;
    demoAlerts = [];
    currentIndex = 0;

    try {
      const res = await fetch('/demo_replay_alerts.json');
      rawAlertTemplates = await res.json();
    } catch (e) {
      console.error("Failed to load demo_replay_alerts.json", e);
      isRunning = false;
      return;
    }

    // Hijack the API completely
    api.getAlerts = async () => ({ alerts: [...demoAlerts], total: demoAlerts.length });
    
    api.getDashboardSummary = async (): Promise<DashboardSummary> => {
      const summary: DashboardSummary = {
        total_alerts: demoAlerts.length,
        critical_count: 0,
        high_count: 0,
        medium_count: 0,
        low_count: 0,
        info_count: 0,
        by_threat_type: {},
        by_detector: {},
        recent_alerts: demoAlerts.slice(0, 100),
      };

      for (const alert of demoAlerts) {
        if (alert.severity === 'critical') summary.critical_count++;
        else if (alert.severity === 'high') summary.high_count++;
        else if (alert.severity === 'medium') summary.medium_count++;
        else if (alert.severity === 'low') summary.low_count++;
        else if (alert.severity === 'info') summary.info_count++;

        summary.by_threat_type[alert.threat_type] = (summary.by_threat_type[alert.threat_type] || 0) + 1;
        summary.by_detector[alert.detector_id] = (summary.by_detector[alert.detector_id] || 0) + 1;
      }

      return summary;
    };

    // Force all components to immediately refetch the now-empty hijacked API
    window.dispatchEvent(new Event('demo-state-changed'));

    // Start the injection loop
    loopInterval = setInterval(() => {
      if (currentIndex >= rawAlertTemplates.length) {
        currentIndex = 0;
      }

      const alertTemplate = rawAlertTemplates[currentIndex];
      const now = new Date();
      
      const liveAlert: Alert = {
        ...alertTemplate,
        alert_id: `DEMO-REPLAY-${Date.now()}-${currentIndex}`,
        timestamp: now.toISOString(),
        detected_at: now.toISOString(),
        last_seen_at: now.toISOString(),
      };

      // Prepend to our hijacked in-memory database
      demoAlerts.unshift(liveAlert);
      
      // Dispatch to the WebSocket mock so Toasts and LiveFeed work
      window.dispatchEvent(new CustomEvent('demo-live-alert', { detail: { alert: liveAlert } }));

      // Dispatch fake telemetry data for the KPI dashboard
      const fakeFlows = Math.floor(Math.random() * (120 - 40 + 1) + 40); // 40-120 flows/sec
      const fakeBytes = fakeFlows * Math.floor(Math.random() * (1500 - 300 + 1) + 300); // Bytes/sec
      window.dispatchEvent(new CustomEvent('demo-live-telemetry', { 
        detail: { 
          flows_per_sec: fakeFlows,
          bytes_per_sec: fakeBytes
        } 
      }));

      currentIndex++;
    }, 800);
  },

  stop: () => {
    if (!isRunning) return;
    isRunning = false;
    if (loopInterval) clearInterval(loopInterval);
    
    // Restore original API
    api.getAlerts = originalGetAlerts;
    api.getDashboardSummary = originalGetDashboardSummary;
    
    // Tell the app to refetch from the real backend
    window.dispatchEvent(new Event('demo-state-changed'));
    window.dispatchEvent(new CustomEvent('demo-live-telemetry', { detail: { flows_per_sec: 0, bytes_per_sec: 0 } }));
  },

  isRunning: () => isRunning,
};
