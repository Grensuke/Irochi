import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAlerts } from '../hooks/useAlerts';
import { STATUS_LABELS, DETECTOR_LABELS } from '../types';
import {
  formatTimestamp,
  formatDate,
  threatLabel,
  formatConfidence,
  confidenceColor,
} from '../utils/format';
import { generateExplanation } from '../utils/explanation';
import { generateRecommendations } from '../utils/recommendations';
import { buildForensicTimeline } from '../utils/correlation';
import { deriveAttackProgression } from '../utils/progression';
import { NarrativePanel } from '../components/NarrativePanel';
import './AlertDetail.css';

export function AlertDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { alerts, loading, error } = useAlerts();

  const [activeAlertId, setActiveAlertId] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (id && !activeAlertId && alerts.length > 0) {
      setActiveAlertId(id);
    }
  }, [id, activeAlertId, alerts]);

  const targetAlert = alerts.find((a) => a.alert_id === id);
  const currentAlert = alerts.find((a) => a.alert_id === (activeAlertId || id));

  const timelineEvents = targetAlert ? buildForensicTimeline(targetAlert, alerts) : [];
  const progression = deriveAttackProgression(timelineEvents);
  const currentIndex = currentAlert ? timelineEvents.findIndex(e => e.alert.alert_id === currentAlert.alert_id) : -1;

  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        if (currentIndex < timelineEvents.length - 1) {
          setActiveAlertId(timelineEvents[currentIndex + 1].alert.alert_id);
        } else {
          setIsPlaying(false);
        }
      }, 2500); // Advance every 2.5s
    }
    return () => clearInterval(interval);
  }, [isPlaying, currentIndex, timelineEvents]);

  const handlePrev = () => {
    if (currentIndex > 0) {
      setActiveAlertId(timelineEvents[currentIndex - 1].alert.alert_id);
    }
  };

  const handleNext = () => {
    if (currentIndex < timelineEvents.length - 1) {
      setActiveAlertId(timelineEvents[currentIndex + 1].alert.alert_id);
    }
  };

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

  if (!targetAlert || !currentAlert) {
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

  const explanation = generateExplanation(currentAlert);
  const recs = generateRecommendations(currentAlert);
  const confPct = formatConfidence(currentAlert.confidence);

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
          <h1 className="mono">INCIDENT OVERVIEW</h1>
          <div className="alert-workspace-tags">
            <span className={`severity-badge ${currentAlert.severity}`}>{currentAlert.severity}</span>
            <span className="threat-badge">{threatLabel(currentAlert.threat_type)}</span>
          </div>
        </div>
        <div className="alert-workspace-meta">
          <div className="meta-block">
            <span className="meta-label">CONFIDENCE</span>
            <span className="meta-value mono" style={{ color: confidenceColor(currentAlert.confidence) }}>{confPct}</span>
          </div>
          <div className="meta-block">
            <span className="meta-label">STATUS</span>
            <span className={`status-text ${currentAlert.status}`}>{STATUS_LABELS[currentAlert.status as keyof typeof STATUS_LABELS]}</span>
          </div>
        </div>
      </div>

      <div className="alert-workspace-grid">
        {/* Left Column: Data & Evidence */}
        <div className="workspace-main">
          
          <NarrativePanel 
            context={{
              alert_id: currentAlert.alert_id,
              detector_id: currentAlert.detector_id,
              threat_type: currentAlert.threat_type,
              severity: currentAlert.severity,
              confidence: currentAlert.confidence,
              src_ip: currentAlert.src_ip,
              dst_ip: currentAlert.dst_ip,
              evidence: currentAlert.evidence,
              explanation,
              progression_stages: progression.stages,
              correlated_events: timelineEvents.map(e => e.alert)
            }}
          />

          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">Event Summary</span>
            </div>
            <div className="panel-body data-grid">
              <div className="data-field">
                <span className="data-label">SOURCE</span>
                <span className="data-value mono">{currentAlert.src_ip ?? '—'}</span>
              </div>
              <div className="data-field">
                <span className="data-label">DESTINATION</span>
                <span className="data-value mono">{currentAlert.dst_ip ?? '—'}</span>
              </div>
              <div className="data-field">
                <span className="data-label">PROTOCOL</span>
                <span className="data-value mono">N/A</span>
              </div>
              <div className="data-field">
                <span className="data-label">DESTINATION PORT</span>
                <span className="data-value mono">{currentAlert.dst_port ?? '—'}</span>
              </div>
              <div className="data-field">
                <span className="data-label">FIRST OBSERVED</span>
                <span className="data-value mono">{formatDate(currentAlert.first_seen_at)} {formatTimestamp(currentAlert.first_seen_at)} UTC</span>
              </div>
              <div className="data-field">
                <span className="data-label">LAST OBSERVED</span>
                <span className="data-value mono">{formatDate(currentAlert.last_seen_at)} {formatTimestamp(currentAlert.last_seen_at)} UTC</span>
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">Explainable Evidence Panel</span>
            </div>
            <div className="panel-body">
              <p className="evidence-summary-text" style={{ fontSize: '1rem', lineHeight: 1.6, marginBottom: '1.5rem', color: 'var(--text)' }}>
                {explanation}
              </p>
              
              {currentAlert.evidence?.signals && Array.isArray(currentAlert.evidence.signals) && (
                <div className="evidence-metrics-grid" style={{ display: 'block', padding: 0 }}>
                  <table className="data-table" style={{ width: '100%', fontSize: '0.85rem' }}>
                    <thead>
                      <tr>
                        <th style={{ textAlign: 'left', padding: '12px' }}>Signal</th>
                        <th style={{ textAlign: 'left', padding: '12px' }}>Observation</th>
                        <th style={{ textAlign: 'left', padding: '12px' }}>Threshold</th>
                        <th style={{ textAlign: 'left', padding: '12px' }}>Trigger State</th>
                      </tr>
                    </thead>
                    <tbody>
                      {currentAlert.evidence.signals.map((sig: any, i: number) => (
                        <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                          <td className="mono" style={{ padding: '12px' }}>{sig.signal_name}</td>
                          <td className="mono" style={{ padding: '12px' }}>{typeof sig.value === 'number' ? sig.value.toFixed(2) : String(sig.value)}</td>
                          <td className="mono" style={{ padding: '12px' }}>{typeof sig.threshold === 'number' ? sig.threshold.toFixed(2) : String(sig.threshold)}</td>
                          <td style={{ padding: '12px' }}>
                            {sig.triggered ? (
                              <span className="severity-badge critical" style={{ fontSize: '0.7rem' }}>TRIGGERED</span>
                            ) : (
                              <span className="severity-badge low" style={{ background: 'var(--surface-3)', fontSize: '0.7rem', color: 'var(--text-muted)' }}>NOT TRIGGERED</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {currentAlert.evidence?.probability !== undefined && (
                <div className="evidence-metrics-grid">
                  <div className="evidence-metric-box">
                    <span className="evidence-metric-label">ML PROBABILITY</span>
                    <span className="evidence-metric-value mono">{((currentAlert.evidence.probability as number) * 100).toFixed(2)}%</span>
                  </div>
                  <div className="evidence-metric-box">
                    <span className="evidence-metric-label">THRESHOLD</span>
                    <span className="evidence-metric-value mono">{((currentAlert.evidence.threshold as number) * 100).toFixed(2)}%</span>
                  </div>
                  {currentAlert.evidence.features_used && Object.entries(currentAlert.evidence.features_used).map(([k, v]) => (
                    <div key={k} className="evidence-metric-box">
                      <span className="evidence-metric-label">{k.toUpperCase()}</span>
                      <span className="evidence-metric-value mono">{typeof v === 'number' ? v.toFixed(2) : String(v)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="panel">
            <div className="panel-header" style={{ borderBottom: '1px solid var(--border)', background: 'rgba(235, 179, 64, 0.05)' }}>
              <span className="panel-title" style={{ color: 'var(--status-warning)' }}>Recommended Immediate Response</span>
            </div>
            <div className="panel-body">
              <ul style={{ margin: 0, paddingLeft: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem', color: 'var(--text)' }}>
                {recs.immediate.map((rec, i) => (
                  <li key={i}>{rec}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="panel">
            <div className="panel-header" style={{ borderBottom: '1px solid var(--border)', background: 'rgba(56, 189, 248, 0.05)' }}>
              <span className="panel-title" style={{ color: 'var(--status-info)' }}>Preventive Recommendations</span>
            </div>
            <div className="panel-body">
              <ul style={{ margin: 0, paddingLeft: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem', color: 'var(--text)' }}>
                {recs.preventive.map((rec, i) => (
                  <li key={i}>{rec}</li>
                ))}
              </ul>
            </div>
          </div>

        </div>

        {/* Right Column: Timeline & Analyst Tools */}
        <div className="workspace-aside">
          
          <div className="panel">
            <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="panel-title">Forensic Investigation Timeline</span>
              
              {timelineEvents.length > 1 && (
                <div className="replay-controls" style={{ display: 'flex', gap: '8px' }}>
                  <button className="btn btn-ghost btn-sm" onClick={handlePrev} disabled={currentIndex === 0}>Prev</button>
                  <button className="btn btn-primary btn-sm" onClick={() => setIsPlaying(!isPlaying)}>
                    {isPlaying ? 'Pause' : 'Play'}
                  </button>
                  <button className="btn btn-ghost btn-sm" onClick={handleNext} disabled={currentIndex === timelineEvents.length - 1}>Next</button>
                </div>
              )}
            </div>

            {progression.stages.length > 0 && (
              <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', display: 'flex', gap: '8px', overflowX: 'auto' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginRight: '8px', alignSelf: 'center' }}>OBSERVED STAGES:</span>
                {progression.stages.map((stage, i) => (
                  <span key={i} className={`severity-badge ${stage.observed ? 'high' : 'low'}`} style={{ opacity: stage.observed ? 1 : 0.4 }}>
                    {stage.name}
                  </span>
                ))}
              </div>
            )}

            <div className="panel-body">
              <div className="vertical-timeline">
                {timelineEvents.length > 0 ? (
                  timelineEvents.map(ev => (
                    <div 
                      key={ev.alert.alert_id} 
                      className={`timeline-step ${ev.alert.alert_id === currentAlert.alert_id ? 'active' : ''}`}
                      onClick={() => setActiveAlertId(ev.alert.alert_id)}
                      style={{ cursor: 'pointer' }}
                    >
                      <span className="timeline-time mono">{formatTimestamp(ev.alert.timestamp)}</span>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <span className="timeline-text" style={{ fontWeight: 600 }}>{DETECTOR_LABELS[ev.alert.detector_id]}</span>
                        <span className="timeline-text" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{threatLabel(ev.alert.threat_type)} detected</span>
                        {ev.reason && (
                          <span className="timeline-text mono" style={{ fontSize: '0.7rem', color: 'var(--status-info)', marginTop: '4px' }}>
                            ↳ {ev.reason}
                          </span>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="timeline-step active">
                    <span className="timeline-time mono">{formatTimestamp(currentAlert.timestamp)}</span>
                    <span className="timeline-text">Alert generated</span>
                  </div>
                )}
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
                <select className="select workspace-select" defaultValue={currentAlert.status}>
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
