
import { useIncidents } from '../hooks/useIncidents';
import type { DashboardSummary } from '../types';
import { THREAT_TYPE_LABELS } from '../types';

interface SecurityPostureProps {
  summary: DashboardSummary | null;
  loading: boolean;
}

export function SecurityPosture({ summary, loading }: SecurityPostureProps) {
  const { incidents, loading: incidentsLoading } = useIncidents('open');

  const isLoading = loading || incidentsLoading;

  let score = 100;
  let isFallback = false;

  if (incidents && incidents.length > 0) {
    const totalRisk = incidents.reduce((sum, inc) => sum + inc.risk_score, 0);
    const avgRisk = totalRisk / incidents.length;
    score = Math.max(0, Math.round(100 - avgRisk));
  } else if (summary) {
    isFallback = true;
    const penalty = 
      (summary.critical_count * 15) + 
      (summary.high_count * 10) + 
      (summary.medium_count * 5) + 
      (summary.low_count * 2);
    score = Math.max(0, 100 - penalty);
  }

  if (isLoading) {
    return (
      <div className="dashboard-kpi" style={{ marginBottom: 'var(--space-4)' }}>
        <div className="kpi-cell">
          <div className="skeleton" style={{ width: 120, height: 16, marginBottom: 8 }} />
          <div className="skeleton" style={{ width: 80, height: 36 }} />
        </div>
      </div>
    );
  }

  // Get breakdown from summary
  const threatTypes = summary?.by_threat_type || {};
  const breakdown = Object.entries(threatTypes)
    .filter(([_, count]) => count > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4);

  return (
    <div className="dashboard-kpi" style={{ marginBottom: 'var(--space-4)' }}>
      <div className="kpi-grid" style={{ gridTemplateColumns: '1fr' }}>
        <div className="kpi-cell" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="kpi-label" style={{ fontSize: '14px' }}>Security Posture Score</span>
            {isFallback && <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>FALLBACK (ALERTS ONLY)</span>}
          </div>
          
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px' }}>
            <span className="kpi-value" style={{ 
              fontSize: '36px', 
              color: score < 50 ? 'var(--severity-critical)' : score < 80 ? 'var(--severity-high)' : 'var(--status-success)'
            }}>
              {score}
            </span>
            <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>/ 100</span>
          </div>

          {breakdown.length > 0 && (
            <div style={{ marginTop: '8px', paddingTop: '12px', borderTop: '1px solid var(--border)' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px', display: 'block' }}>
                Active Threat Categories
              </span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {breakdown.map(([tt, count]) => (
                  <div key={tt} style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'var(--surface-3)', padding: '2px 6px', borderRadius: '4px', fontSize: '11px' }}>
                    <span style={{ color: 'var(--text-primary)' }}>{THREAT_TYPE_LABELS[tt as keyof typeof THREAT_TYPE_LABELS] || tt}</span>
                    <span style={{ color: 'var(--text-muted)' }}>({count})</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
