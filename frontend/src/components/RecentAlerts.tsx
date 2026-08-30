/**
 * RecentAlerts — compact dashboard widget.
 *
 * Displays the 5 most recent alerts from the dashboard summary.
 * Clicking a row navigates to the full alert detail page.
 * This is intentionally lightweight; the full AlertTable lives on /app/alerts.
 */

import { useNavigate } from 'react-router-dom';
import type { Alert } from '../types';
import { STATUS_LABELS } from '../types';
import {
  formatTimestamp,
  formatDate,
  threatLabel,
  formatConfidence,
  confidenceColor,
} from '../utils/format';

interface RecentAlertsProps {
  alerts: Alert[];
  loading: boolean;
}

export function RecentAlerts({ alerts, loading }: RecentAlertsProps) {
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title">Recent Alerts</span>
        </div>
        <div className="panel-body">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="skeleton" style={{ height: 32, marginBottom: 6 }} />
          ))}
        </div>
      </div>
    );
  }

  if (alerts.length === 0) {
    return (
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title">Recent Alerts</span>
        </div>
        <div className="state-message">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 12l2 2 4-4" />
            <circle cx="12" cy="12" r="10" />
          </svg>
          <span className="state-title">No alerts detected</span>
          <span className="state-detail">No threat alerts have been observed.</span>
        </div>
      </div>
    );
  }

  const recent = alerts.slice(0, 5);

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Recent Alerts</span>
        <button
          className="btn btn-ghost btn-sm"
          onClick={() => navigate('/app/alerts')}
          aria-label="View all alerts"
        >
          View all
        </button>
      </div>
      <div className="recent-alerts-list">
        {recent.map((alert) => (
          <button
            key={alert.alert_id}
            className="recent-alert-row"
            onClick={() => navigate(`/app/alerts/${alert.alert_id}`)}
            aria-label={`Open alert ${alert.alert_id}`}
          >
            <span className={`severity-badge ${alert.severity}`}>{alert.severity}</span>
            <span className="recent-alert-meta">
              <span className="recent-alert-type">{threatLabel(alert.threat_type)}</span>
              <span className="recent-alert-id mono">{alert.alert_id}</span>
            </span>
            <span className="recent-alert-right">
              <span
                className="mono"
                style={{ color: confidenceColor(alert.confidence) }}
              >
                {formatConfidence(alert.confidence)}
              </span>
              <span className="recent-alert-time mono">
                {formatDate(alert.timestamp)} {formatTimestamp(alert.timestamp)}
              </span>
              <span className={`status-text ${alert.status}`}>
                {STATUS_LABELS[alert.status]}
              </span>
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
