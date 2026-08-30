import type { Alert } from '../types';
import { STATUS_LABELS } from '../types';
import { formatTimestamp, formatDate, threatLabel, detectorLabel, formatConfidence, confidenceColor } from '../utils/format';
import './AlertDetail.css';

interface AlertDetailProps {
  alert: Alert;
  onClose: () => void;
}

export function AlertDetail({ alert, onClose }: AlertDetailProps) {
  return (
    <div className="alert-detail-overlay" onClick={onClose} role="presentation">
      <div className="alert-detail-panel animate-slide-in" onClick={(e) => e.stopPropagation()}>
        <div className="detail-header">
          <div className="detail-header-left">
            <span className={`severity-badge ${alert.severity}`}>{alert.severity}</span>
            <span className="mono detail-alert-id">{alert.alert_id}</span>
          </div>
          <button className="detail-close" onClick={onClose} aria-label="Close alert detail">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="4" y1="4" x2="12" y2="12" />
              <line x1="12" y1="4" x2="4" y2="12" />
            </svg>
          </button>
        </div>

        <div className="detail-body">
          <div className="detail-grid">
            <div className="detail-field">
              <span className="detail-label">Threat Type</span>
              <span className="detail-value">{threatLabel(alert.threat_type)}</span>
            </div>
            <div className="detail-field">
              <span className="detail-label">Detector</span>
              <span className="detail-value">{detectorLabel(alert.detector_id)}</span>
            </div>
            <div className="detail-field">
              <span className="detail-label">Timestamp</span>
              <span className="detail-value mono">{formatDate(alert.timestamp)} {formatTimestamp(alert.timestamp)}</span>
            </div>
            <div className="detail-field">
              <span className="detail-label">Status</span>
              <span className={`status-text ${alert.status}`}>{STATUS_LABELS[alert.status]}</span>
            </div>
            <div className="detail-field">
              <span className="detail-label">Confidence</span>
              <div className="detail-confidence">
                <span className="mono" style={{ color: confidenceColor(alert.confidence) }}>
                  {formatConfidence(alert.confidence)}
                </span>
                <div className="confidence-bar" style={{ width: 80 }}>
                  <div
                    className="confidence-fill"
                    style={{
                      width: `${(alert.confidence ?? 0) * 100}%`,
                      background: confidenceColor(alert.confidence),
                    }}
                  />
                </div>
              </div>
            </div>
            <div className="detail-field">
              <span className="detail-label">Source</span>
              <span className="detail-value mono">
                {alert.src_ip ?? '—'}{alert.src_port ? `:${alert.src_port}` : ''}
              </span>
            </div>
            <div className="detail-field">
              <span className="detail-label">Destination</span>
              <span className="detail-value mono">
                {alert.dst_ip ?? '—'}{alert.dst_port ? `:${alert.dst_port}` : ''}
              </span>
            </div>
          </div>

          <div className="detail-evidence">
            <span className="detail-label">Evidence Summary</span>
            <p className="detail-evidence-text">{alert.evidence_summary}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
