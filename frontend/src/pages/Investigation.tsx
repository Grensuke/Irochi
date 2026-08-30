/**
 * Investigation page.
 *
 * Provides a per-alert investigation workspace.
 * Uses route state or URL param to load an alert and display its evidence.
 * All evidence is MOCK/DEMO until the backend evidence pipeline is implemented.
 */

import { useNavigate } from 'react-router-dom';
import { useAlerts } from '../hooks/useAlerts';
import { STATUS_LABELS } from '../types';
import {
  formatTimestamp,
  formatDate,
  threatLabel,
  formatConfidence,
  confidenceColor,
} from '../utils/format';
import { MOCK_EVIDENCE_BY_ALERT } from '../services/mockData';

export function Investigation() {
  const navigate = useNavigate();
  const { alerts, loading, error } = useAlerts();

  if (loading) {
    return (
      <div className="investigation-page">
        <div className="skeleton" style={{ height: 200, borderRadius: 8 }} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="investigation-page">
        <div className="state-message">
          <span className="state-title">Failed to load alerts</span>
          <span className="state-detail">{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="investigation-page">
      <div className="demo-banner" role="status">
        Evidence data shown is DEMO/MOCK — a real evidence pipeline is not yet connected.
      </div>

      <div className="panel">
        <div className="panel-header">
          <span className="panel-title">Select an Alert to Investigate</span>
          <span className="panel-title" style={{ opacity: 0.5 }}>{alerts.length}</span>
        </div>
        <div className="investigation-list">
          {alerts.map((alert) => {
            const evidence =
              MOCK_EVIDENCE_BY_ALERT[alert.alert_id] ??
              MOCK_EVIDENCE_BY_ALERT['default'];
            return (
              <div key={alert.alert_id} className="investigation-item">
                <div className="investigation-item-header">
                  <span className={`severity-badge ${alert.severity}`}>
                    {alert.severity}
                  </span>
                  <span className="mono investigation-id">{alert.alert_id}</span>
                  <span className="investigation-type">
                    {threatLabel(alert.threat_type)}
                  </span>
                  <span
                    className="mono"
                    style={{ color: confidenceColor(alert.confidence) }}
                  >
                    {formatConfidence(alert.confidence)}
                  </span>
                  <span className="mono investigation-time">
                    {formatDate(alert.timestamp)} {formatTimestamp(alert.timestamp)}
                  </span>
                  <span className={`status-text ${alert.status}`}>
                    {STATUS_LABELS[alert.status]}
                  </span>
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={() => navigate(`/app/alerts/${alert.alert_id}`)}
                    aria-label={`Open full detail for ${alert.alert_id}`}
                  >
                    Full detail
                  </button>
                </div>
                <div className="investigation-evidence">
                  <span className="detail-label">Supporting Observations</span>
                  <ul className="evidence-list">
                    {evidence.map((line, i) => (
                      <li key={i} className="evidence-list-item mono">{line}</li>
                    ))}
                  </ul>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
