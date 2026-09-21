import { useNavigate } from 'react-router-dom';
import { useIncidents } from '../hooks/useIncidents';
import { THREAT_TYPE_LABELS } from '../types';
import { formatDate, formatTimestamp } from '../utils/format';
import { ShieldAlert, ArrowRight, Shield, ShieldCheck, Activity, Target, ShieldQuestion, Loader2 } from 'lucide-react';

export function Investigation() {
  const navigate = useNavigate();
  const { incidents, loading, error } = useIncidents();

  if (loading) {
    return (
      <div className="investigation-page">
        <div className="state-message">
          <Loader2 className="connecting-spinner" />
          <div className="state-title">Loading Investigation Queue</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="investigation-page">
        <div className="state-message" style={{ color: 'var(--status-error)' }}>
          <ShieldAlert />
          <div className="state-title">Failed to load incidents</div>
          <div className="state-detail">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="page-header">
        <h1>Incident Investigation Queue</h1>
        <div className="page-header-actions">
          <span className="demo-badge">{incidents.length} Open Incidents</span>
        </div>
      </div>

      <div className="investigation-page">
        <div className="panel">
          <div className="panel-header">
            <h2 className="panel-title">Active Investigations</h2>
          </div>
          
          <div className="investigation-list">
            {incidents.map((incident) => {
              const isAttack = incident.stage_state === 'likely_attack' || incident.stage_state === 'confirmed_attack';
              
              // Icon based on stage
              let StageIcon = ShieldQuestion;
              if (incident.stage_state === 'confirmed_attack') StageIcon = ShieldAlert;
              else if (incident.stage_state === 'likely_attack') StageIcon = Shield;
              else if (incident.stage_state === 'anomaly') StageIcon = Activity;
              else if (incident.stage_state === 'suspicious') StageIcon = Target;

              return (
                <div key={incident.incident_id} className="investigation-item" style={{ display: 'flex', gap: 'var(--space-5)', alignItems: 'center' }}>
                  
                  {/* KPI Risk Score Cell */}
                  <div className="kpi-cell" style={{ borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', minWidth: '110px', alignItems: 'center' }}>
                    <div className="kpi-value" style={{ color: incident.risk_score > 70 ? 'var(--severity-critical)' : incident.risk_score > 40 ? 'var(--severity-high)' : 'var(--text-primary)' }}>
                      {Math.round(incident.risk_score)}
                    </div>
                    <div className="kpi-label uppercase">Risk Score</div>
                  </div>

                  {/* Incident Details */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div className="investigation-item-header" style={{ marginBottom: 'var(--space-2)' }}>
                      <span className={`phase-badge ${isAttack ? 'live' : 'backfill'}`} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <StageIcon size={12} />
                        {incident.stage_state.replace('_', ' ')}
                      </span>
                      <span className="investigation-type mono" style={{ fontSize: '0.85rem' }}>
                        {incident.entity_key} <span style={{ color: 'var(--text-muted)' }}>({incident.entity_type})</span>
                      </span>
                    </div>

                    <div className="investigation-evidence" style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)', marginBottom: 'var(--space-3)' }}>
                      {incident.distinct_threat_types.map(tt => (
                        <span key={tt} className="threat-tag">
                          {THREAT_TYPE_LABELS[tt] || tt}
                        </span>
                      ))}
                    </div>

                    <div className="investigation-time" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', fontFamily: 'var(--font-mono)' }}>
                      <span>Alerts: {incident.member_alert_ids.length}</span>
                      <span style={{ opacity: 0.5 }}>|</span>
                      <span>Last Active: {formatDate(incident.last_event_at)} {formatTimestamp(incident.last_event_at)}</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div style={{ flexShrink: 0 }}>
                    <button 
                      className="btn btn-primary"
                      onClick={() => {
                        if (incident.member_alert_ids.length > 0) {
                          navigate(`/app/alerts/${incident.member_alert_ids[0]}`);
                        }
                      }}
                      disabled={incident.member_alert_ids.length === 0}
                    >
                      Investigate <ArrowRight size={14} />
                    </button>
                  </div>
                </div>
              );
            })}
            
            {incidents.length === 0 && (
              <div className="state-message">
                <ShieldCheck size={48} style={{ color: 'var(--accent-green)', opacity: 0.8 }} />
                <div className="state-title">No Active Incidents</div>
                <div className="state-detail">The incident queue is clear. No active threats detected in the monitored traffic.</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
