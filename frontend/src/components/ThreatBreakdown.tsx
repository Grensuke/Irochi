import type { DashboardSummary } from '../types';
import { THREAT_TYPE_LABELS } from '../types';
import './ThreatBreakdown.css';

interface ThreatBreakdownProps {
  summary: DashboardSummary | null;
  loading: boolean;
}

export function ThreatBreakdown({ summary, loading }: ThreatBreakdownProps) {
  if (loading || !summary) {
    return (
      <div className="panel" style={{ height: '100%' }}>
        <div className="panel-header">
          <span className="panel-title">Threat Distribution</span>
        </div>
        <div className="panel-body">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} style={{ marginBottom: 16 }}>
              <div className="skeleton" style={{ width: '40%', height: 12, marginBottom: 8 }} />
              <div className="skeleton" style={{ width: '100%', height: 4 }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const { by_threat_type } = summary;
  const entries = Object.entries(by_threat_type);
  
  if (entries.length === 0) {
    return (
      <div className="panel" style={{ height: '100%' }}>
        <div className="panel-header">
          <span className="panel-title">Threat Distribution</span>
        </div>
        <div className="state-message">
          <span className="state-title">No Threats Detected</span>
        </div>
      </div>
    );
  }

  // Sort by count descending
  entries.sort((a, b) => b[1] - a[1]);
  const maxCount = Math.max(...entries.map(e => e[1]));
  const totalCount = entries.reduce((acc, curr) => acc + curr[1], 0);

  return (
    <div className="panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header">
        <span className="panel-title">Threat Distribution</span>
      </div>
      <div className="panel-body" style={{ flex: 1 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {entries.map(([type, count]) => {
            const pct = Math.round((count / totalCount) * 100);
            const fillWidth = `${(count / maxCount) * 100}%`;
            
            return (
              <div key={type} className="threat-hbar-row">
                <span className="threat-hbar-label" title={THREAT_TYPE_LABELS[type as keyof typeof THREAT_TYPE_LABELS] || type}>
                  {THREAT_TYPE_LABELS[type as keyof typeof THREAT_TYPE_LABELS] || type}
                </span>
                <div className="threat-hbar-track">
                  <div className="threat-hbar-fill" style={{ width: fillWidth, background: 'var(--accent-primary)' }} />
                </div>
                <span className="threat-hbar-count">
                  {pct}%
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
