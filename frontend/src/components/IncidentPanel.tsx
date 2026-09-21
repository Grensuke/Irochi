
import type { Incident, ThreatType } from '../types';
import { AlertTriangle, TrendingUp, ShieldAlert } from 'lucide-react';
import { THREAT_TYPE_LABELS } from '../types';
import { KPIMetric } from './KPIMetric';

interface IncidentPanelProps {
  incident: Incident;
  onClose?: () => void;
  isClosing?: boolean;
}

export function IncidentPanel({ incident, onClose, isClosing }: IncidentPanelProps) {
  const isAttack = incident.stage_state === 'likely_attack' || incident.stage_state === 'confirmed_attack';

  return (
    <div className="panel">
      <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldAlert size={16} style={{ color: 'var(--accent)' }} />
          Incident Context
        </span>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span className={`severity-badge ${isAttack ? 'critical' : 'warning'}`} style={{ textTransform: 'uppercase' }}>
            {incident.stage_state.replace('_', ' ')}
          </span>
          {incident.status === 'open' && onClose && (
            <button 
              className="btn btn-sm btn-ghost" 
              onClick={onClose} 
              disabled={isClosing}
              style={{ padding: '2px 8px', fontSize: '0.75rem', height: 'auto', border: '1px solid var(--border)' }}
            >
              {isClosing ? 'Closing...' : 'Close Incident'}
            </button>
          )}
          {incident.status === 'closed' && (
            <span className="severity-badge" style={{ background: 'var(--surface-3)', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Closed
            </span>
          )}
        </div>
      </div>

      <div className="panel-body">
        <div className="dashboard-kpi" style={{ borderBottom: '1px solid var(--border)', paddingBottom: '16px', marginBottom: '16px', marginTop: '-12px', background: 'transparent' }}>
          <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
            <KPIMetric 
              label="Risk Score" 
              value={`${Math.round(incident.risk_score)}/100`} 
            />
            <KPIMetric 
              label="Correlated Alerts" 
              value={incident.member_alert_ids.length} 
            />
            <KPIMetric 
              label="Current Stage" 
              value={incident.current_stage ? (THREAT_TYPE_LABELS[incident.current_stage as ThreatType] || incident.current_stage) : 'None'} 
            />
          </div>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase' }}>
            Threat Types Present
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {incident.distinct_threat_types.map(tt => (
              <span key={tt} className="severity-badge high" style={{ background: 'var(--surface-3)' }}>
                {THREAT_TYPE_LABELS[tt] || tt}
              </span>
            ))}
          </div>
        </div>

        {incident.forecast_next_stage && (
          <div style={{ background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.1)', borderRadius: '6px', padding: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--status-critical)', fontSize: '0.85rem', fontWeight: 600, marginBottom: '4px' }}>
              <TrendingUp size={14} />
              Risk Forecast (Next Stage)
            </div>
            <div style={{ color: 'var(--text)', fontWeight: 500, marginBottom: '8px' }}>
              {THREAT_TYPE_LABELS[incident.forecast_next_stage as ThreatType] || incident.forecast_next_stage}
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '6px', color: 'var(--status-critical)', opacity: 0.8, fontSize: '0.75rem', lineHeight: 1.4 }}>
              <AlertTriangle size={12} style={{ marginTop: '2px', flexShrink: 0 }} />
              <span>* [EXPERIMENTAL] Forecast is a probabilistic projection based on observed kill-chain progression, not a claim that the next stage has occurred.</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
