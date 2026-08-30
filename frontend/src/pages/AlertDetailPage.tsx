import { useNavigate, useParams } from 'react-router-dom';
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
import './AlertDetail.css';

export function AlertDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { alerts, loading, error } = useAlerts();

  if (loading) {
    return (
      <div className="detail-page">
        <div className="skeleton" style={{ height: 200, borderRadius: 8 }} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="detail-page">
        <div className="state-message">
          <span className="state-title">Failed to load alert</span>
          <span className="state-detail">{error}</span>
        </div>
      </div>
    );
  }

  const alert = alerts.find((a) => a.alert_id === id);

  if (!alert) {
    return (
      <div className="detail-page">
        <div className="state-message">
          <span className="state-title">Alert not found</span>
          <span className="state-detail">No alert with ID {id} was found.</span>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/app/alerts')}>
            Back to Alerts
          </button>
        </div>
      </div>
    );
  }

  const evidence = MOCK_EVIDENCE_BY_ALERT[alert.alert_id] ?? MOCK_EVIDENCE_BY_ALERT['default'];
  const confPct = formatConfidence(alert.confidence);

  return (
    <div className="detail-page">
      <button
        className="btn btn-ghost btn-sm detail-page-back"
        onClick={() => navigate(-1)}
        aria-label="Go back"
      >
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="10,3 5,8 10,13" />
        </svg>
        Back
      </button>

      {/* Main Alert Header */}
      <div className="alert-workspace-header">
        <div className="alert-workspace-title">
          <h1 className="mono">ALERT {alert.alert_id}</h1>
          <div className="alert-workspace-tags">
            <span className={`severity-badge ${alert.severity}`}>{alert.severity}</span>
            <span className="threat-badge">{threatLabel(alert.threat_type)}</span>
          </div>
        </div>
        <div className="alert-workspace-meta">
          <div className="meta-block">
            <span className="meta-label">CONFIDENCE</span>
            <span className="meta-value mono" style={{ color: confidenceColor(alert.confidence) }}>{confPct}</span>
          </div>
          <div className="meta-block">
            <span className="meta-label">STATUS</span>
            <span className={`status-text ${alert.status}`}>{STATUS_LABELS[alert.status]}</span>
          </div>
        </div>
      </div>

      <div className="alert-workspace-grid">
        {/* Left Column: Data & Evidence */}
        <div className="workspace-main">
          
          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">Event Summary</span>
            </div>
            <div className="panel-body data-grid">
              <div className="data-field">
                <span className="data-label">SOURCE</span>
                <span className="data-value mono">{alert.src_ip ?? '—'}</span>
              </div>
              <div className="data-field">
                <span className="data-label">DESTINATION</span>
                <span className="data-value mono">{alert.dst_ip ?? '—'}</span>
              </div>
              <div className="data-field">
                <span className="data-label">PROTOCOL</span>
                <span className="data-value mono">{alert.proto ?? 'TCP'}</span>
              </div>
              <div className="data-field">
                <span className="data-label">DESTINATION PORT</span>
                <span className="data-value mono">{alert.dst_port ?? '—'}</span>
              </div>
              <div className="data-field">
                <span className="data-label">FIRST OBSERVED</span>
                <span className="data-value mono">{formatDate(alert.timestamp)} {formatTimestamp(alert.timestamp)} UTC</span>
              </div>
              <div className="data-field">
                <span className="data-label">LAST OBSERVED</span>
                <span className="data-value mono">{formatDate(alert.timestamp)} {formatTimestamp(alert.timestamp)} UTC</span>
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">Detection Evidence</span>
            </div>
            <div className="panel-body">
              <p className="evidence-summary-text">{alert.evidence_summary}</p>
              <div className="evidence-metrics-grid">
                {evidence.map((line, i) => (
                  <div key={i} className="evidence-metric-box">
                    <span className="evidence-metric-label">OBSERVATION {i + 1}</span>
                    <span className="evidence-metric-value mono">{line}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">Model Decision</span>
            </div>
            <div className="panel-body model-decision-box">
              <div className="model-decision-top">
                <div>
                  <span className="md-label">THREAT:</span>
                  <span className="md-value">{threatLabel(alert.threat_type)}</span>
                </div>
                <div>
                  <span className="md-label">CONFIDENCE:</span>
                  <span className="md-value mono" style={{ color: confidenceColor(alert.confidence) }}>{confPct}</span>
                </div>
              </div>
              <p className="model-decision-desc">
                Traffic characteristics strongly match the learned {threatLabel(alert.threat_type).toLowerCase()} profile based on the observed evidence.
              </p>
            </div>
          </div>

        </div>

        {/* Right Column: Timeline & Analyst Tools */}
        <div className="workspace-aside">
          
          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">Investigation Timeline</span>
            </div>
            <div className="panel-body">
              <div className="vertical-timeline">
                <div className="timeline-step">
                  <span className="timeline-time mono">{formatTimestamp(alert.timestamp)}</span>
                  <span className="timeline-text">Anomalous activity detected</span>
                </div>
                <div className="timeline-step">
                  <span className="timeline-time mono">{formatTimestamp(alert.timestamp)}</span>
                  <span className="timeline-text">Traffic rate exceeded baseline</span>
                </div>
                <div className="timeline-step">
                  <span className="timeline-time mono">{formatTimestamp(alert.timestamp)}</span>
                  <span className="timeline-text">Detector confidence increased</span>
                </div>
                <div className="timeline-step active">
                  <span className="timeline-time mono">{formatTimestamp(alert.timestamp)}</span>
                  <span className="timeline-text">Alert generated</span>
                </div>
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">Analyst Workspace</span>
            </div>
            <div className="panel-body analyst-workspace-body">
              <div className="workspace-field">
                <label className="data-label">STATUS</label>
                <select className="select workspace-select" defaultValue={alert.status}>
                  {Object.entries(STATUS_LABELS).map(([k, v]) => (
                    <option key={k} value={k}>{v}</option>
                  ))}
                </select>
              </div>
              <div className="workspace-field">
                <label className="data-label">ANALYST NOTES</label>
                <textarea className="input workspace-textarea" placeholder="Add investigation notes..."></textarea>
              </div>
              <button className="btn btn-primary" style={{ width: '100%' }}>Save Investigation</button>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
