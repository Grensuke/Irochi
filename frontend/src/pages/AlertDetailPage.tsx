import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAlerts } from '../hooks/useAlerts';
import { useIncident } from '../hooks/useIncident';
import { api } from '../services/api';
import type { Alert } from '../types';
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
import { exportAlertToPdf } from '../utils/exportPdf';
import { NarrativePanel } from '../components/NarrativePanel';
import { IncidentPanel } from '../components/IncidentPanel';
import { EvidenceChain } from '../components/EvidenceChain';
import './AlertDetail.css';

export function AlertDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { alerts, loading, error } = useAlerts();

  const [activeAlertId, setActiveAlertId] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [narrativeData, setNarrativeData] = useState<{ what_was_observed: string; why_it_matters: string; what_to_investigate: string } | null>(null);

  useEffect(() => {
    if (id && !activeAlertId && alerts.length > 0) {
      setActiveAlertId(id);
    }
  }, [id, activeAlertId, alerts]);

  const targetAlert = alerts.find((a) => a.alert_id === id);

  const { incident, loading: incidentLoading } = useIncident(targetAlert?.incident_id);

  const [memberAlerts, setMemberAlerts] = useState<Alert[]>([]);
  const [memberAlertsLoading, setMemberAlertsLoading] = useState(false);

  useEffect(() => {
    if (incident?.member_alert_ids) {
      setMemberAlertsLoading(true);
      Promise.all(incident.member_alert_ids.map(mid => api.getAlert(mid)))
        .then(results => {
          const sorted = results.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
          setMemberAlerts(sorted);
        })
        .catch(err => console.error("Failed to load member alerts", err))
        .finally(() => setMemberAlertsLoading(false));
    }
  }, [incident]);

  // Use incident sequence if available, otherwise fallback to isolated timeline logic
  const timelineEvents = incident && memberAlerts.length > 0
    ? memberAlerts.map(a => ({ alert: a, reason: '' }))
    : targetAlert ? buildForensicTimeline(targetAlert, alerts) : [];

  const progression = deriveAttackProgression(timelineEvents);
  
  // Find current index based on activeAlertId (or fallback to targetAlert id)
  const currentAlertId = activeAlertId || id;
  const currentIndex = timelineEvents.findIndex(e => e.alert.alert_id === currentAlertId);
  const currentAlert = currentIndex !== -1 
    ? timelineEvents[currentIndex].alert 
    : (targetAlert || null);

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

  // Export to PDF handler
  const handleExportPdf = async () => {
    if (!currentAlert) return;
    setIsExporting(true);
    try {
      // Fetch narrative data for the PDF (same payload as NarrativePanel)
      let narrative = narrativeData;
      if (!narrative) {
        try {
          narrative = await api.generateNarrative({
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
          });
          setNarrativeData(narrative);
        } catch {
          // Narrative API might fail, proceed without it
          narrative = null;
        }
      }

      exportAlertToPdf({
        alert: currentAlert,
        incident: incident || null,
        timelineEvents,
        narrative,
        explanation,
        recommendations: recs,
      });
    } catch (err) {
      console.error('PDF export failed:', err);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="detail-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
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
        <button
          className="btn btn-primary btn-sm"
          onClick={handleExportPdf}
          disabled={isExporting}
          style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 14px' }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
          {isExporting ? 'Generating...' : 'Export to PDF'}
        </button>
      </div>

      {/* Main Alert Header */}
      <div className="alert-workspace-header">
        <div className="alert-workspace-title">
          <h1 className="mono">INCIDENT OVERVIEW</h1>
          <div className="alert-workspace-tags">
            <span className={`severity-badge ${currentAlert.severity}`}>SEVERITY: {currentAlert.severity.toUpperCase()}</span>
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
          
          {incident && (
            <div className="mb-6 space-y-6">
              <IncidentPanel incident={incident} />
              <EvidenceChain incident={incident} />
            </div>
          )}

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

            <div className="panel-body" style={{ paddingTop: 'var(--space-4)' }}>
              <div className="alert-timeline">
                {timelineEvents.length > 0 ? (
                  timelineEvents.map((ev, index) => {
                    const isActive = ev.alert.alert_id === currentAlert.alert_id;
                    const isPast = index < currentIndex;
                    
                    let dotClass = 'pending';
                    if (isActive) dotClass = 'active';
                    else if (isPast) dotClass = 'done';
                    if (ev.alert.status === 'false_positive') dotClass = 'false-pos';

                    return (
                      <div 
                        key={ev.alert.alert_id} 
                        className={`timeline-step ${isActive ? 'active' : ''}`}
                        onClick={() => setActiveAlertId(ev.alert.alert_id)}
                        style={{ cursor: 'pointer', opacity: isPast || isActive ? 1 : 0.6, transition: 'all 200ms ease' }}
                      >
                        <div className={`timeline-dot ${dotClass}`}></div>
                        <div className="timeline-content" style={{ width: '100%' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <span className="timeline-label">{DETECTOR_LABELS[ev.alert.detector_id] || ev.alert.detector_id}</span>
                            <span className="timeline-time">{formatTimestamp(ev.alert.timestamp)}</span>
                          </div>
                          
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                            <span className={`severity-badge ${ev.alert.severity}`} style={{ fontSize: '0.65rem', padding: '1px 6px' }}>
                              SEVERITY: {ev.alert.severity.toUpperCase()}
                            </span>
                            <span className="timeline-note" style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                              {threatLabel(ev.alert.threat_type)}
                            </span>
                          </div>

                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '8px', padding: '8px', background: isActive ? 'var(--bg-active)' : 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', fontFamily: 'var(--font-mono)' }}>
                              <span style={{ color: 'var(--text-muted)' }}>SRC:</span>
                              <span style={{ color: 'var(--text-secondary)' }}>{ev.alert.src_ip || 'N/A'}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', fontFamily: 'var(--font-mono)' }}>
                              <span style={{ color: 'var(--text-muted)' }}>DST:</span>
                              <span style={{ color: 'var(--text-secondary)' }}>{ev.alert.dst_ip || 'N/A'}{ev.alert.dst_port ? `:${ev.alert.dst_port}` : ''}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', fontFamily: 'var(--font-mono)' }}>
                              <span style={{ color: 'var(--text-muted)' }}>CONFIDENCE:</span>
                              <span style={{ color: confidenceColor(ev.alert.confidence), fontWeight: 600 }}>{formatConfidence(ev.alert.confidence)}</span>
                            </div>
                          </div>

                          {ev.reason && (
                            <span className="timeline-note mono" style={{ fontSize: '0.7rem', color: 'var(--status-info)', marginTop: '6px' }}>
                              ↳ {ev.reason}
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="timeline-step active">
                    <div className="timeline-dot active"></div>
                    <div className="timeline-content">
                      <span className="timeline-time mono">{formatTimestamp(currentAlert.timestamp)}</span>
                      <span className="timeline-label">Alert generated</span>
                      <span className="timeline-note">No correlation data available</span>
                    </div>
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
