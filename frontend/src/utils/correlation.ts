import type { Alert } from '../types';

export interface CorrelatedEvent {
  alert: Alert;
  reason: string;
}

const CORRELATION_WINDOW_MS = 60 * 60 * 1000; // 1 hour

export function buildForensicTimeline(targetAlert: Alert, allAlerts: Alert[]): CorrelatedEvent[] {
  const correlated: CorrelatedEvent[] = [];
  const targetTime = new Date(targetAlert.timestamp).getTime();

  for (const a of allAlerts) {
    if (a.alert_id === targetAlert.alert_id) {
      correlated.push({ alert: a, reason: 'Current investigation target.' });
      continue;
    }

    const aTime = new Date(a.timestamp).getTime();
    const timeDiff = Math.abs(aTime - targetTime);

    // We only correlate within the window
    if (timeDiff <= CORRELATION_WINDOW_MS) {
      const minutes = Math.max(1, Math.round(timeDiff / 60000));
      
      if (a.src_ip && a.src_ip === targetAlert.src_ip) {
        correlated.push({
          alert: a,
          reason: `Related because source IP matches and events occurred within ${minutes} minutes.`
        });
        continue;
      }

      if (a.dst_ip && a.dst_ip === targetAlert.dst_ip && targetAlert.dst_ip) {
         correlated.push({
          alert: a,
          reason: `Related because destination IP matches and events occurred within ${minutes} minutes.`
        });
        continue;
      }
      
      // If same detector but unrelated entities, DO NOT merge.
    }
  }

  // Sort chronologically
  return correlated.sort((a, b) => new Date(a.alert.timestamp).getTime() - new Date(b.alert.timestamp).getTime());
}
