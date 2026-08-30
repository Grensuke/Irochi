import { useState } from 'react';
import { STATUS_LABELS } from '../types';
import type { Alert } from '../types';
import { formatTimestamp, formatDate, threatLabel, formatConfidence, confidenceColor } from '../utils/format';
import { AlertDetail } from './AlertDetail';
import './AlertTable.css';

interface AlertTableProps {
  alerts: Alert[];
  loading: boolean;
  error: string | null;
  title?: string;
}

export function AlertTable({ alerts, loading, error, title = 'Recent Alerts' }: AlertTableProps) {
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);

  if (loading) {
    return (
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title">{title}</span>
        </div>
        <div className="panel-body">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="alert-row-skeleton">
              <div className="skeleton" style={{ width: '100%', height: 36 }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title">{title}</span>
        </div>
        <div className="state-message">
          <svg viewBox="0 0 24 24" fill="none" stroke="var(--status-error)" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span className="state-title">Failed to load alerts</span>
          <span className="state-detail">{error}</span>
        </div>
      </div>
    );
  }

  if (alerts.length === 0) {
    return (
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title">{title}</span>
        </div>
        <div className="state-message">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 12l2 2 4-4" />
            <circle cx="12" cy="12" r="10" />
          </svg>
          <span className="state-title">No alerts</span>
          <span className="state-detail">No threat alerts have been detected.</span>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title">{title}</span>
          <span className="panel-title" style={{ opacity: 0.5 }}>{alerts.length}</span>
        </div>
        <div className="alert-table-wrap">
          <table className="alert-table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>Time</th>
                <th>ID</th>
                <th>Threat Type</th>
                <th>Confidence</th>
                <th>Source</th>
                <th>Destination</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((alert) => (
                <tr
                  key={alert.alert_id}
                  className="alert-row"
                  onClick={() => setSelectedAlert(alert)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === 'Enter' && setSelectedAlert(alert)}
                >
                  <td>
                    <span className={`severity-badge ${alert.severity}`}>{alert.severity}</span>
                  </td>
                  <td className="mono">
                    <span className="alert-date">{formatDate(alert.timestamp)}</span>
                    <span className="alert-time">{formatTimestamp(alert.timestamp)}</span>
                  </td>
                  <td className="mono alert-id-cell">{alert.alert_id}</td>
                  <td>{threatLabel(alert.threat_type)}</td>
                  <td>
                    <div className="confidence-cell">
                      <span className="mono">{formatConfidence(alert.confidence)}</span>
                      <div className="confidence-bar">
                        <div
                          className="confidence-fill"
                          style={{
                            width: `${(alert.confidence ?? 0) * 100}%`,
                            background: confidenceColor(alert.confidence),
                          }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="mono">{alert.src_ip ?? '—'}</td>
                  <td className="mono">
                    {alert.dst_ip ?? '—'}
                    {alert.dst_port ? `:${alert.dst_port}` : ''}
                  </td>
                  <td>
                    <span className={`status-text ${alert.status}`}>{STATUS_LABELS[alert.status]}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selectedAlert && (
        <AlertDetail alert={selectedAlert} onClose={() => setSelectedAlert(null)} />
      )}
    </>
  );
}
