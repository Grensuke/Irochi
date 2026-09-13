import type { DashboardSummary } from '../types';
import { SEVERITY_ORDER } from '../types';
import { severityColor } from '../utils/format';

interface SeverityDistributionProps {
  summary: DashboardSummary | null;
  loading?: boolean;
}

export function SeverityDistribution({ summary, loading }: SeverityDistributionProps) {
  if (loading || !summary) {
    return (
      <div className="panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <div className="panel-header" style={{ borderBottom: 'none' }}>
          <span className="panel-title">SEVERITY DISTRIBUTION</span>
        </div>
        <div className="panel-content" style={{ flex: 1, padding: 'var(--space-4)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Loading...</span>
        </div>
      </div>
    );
  }

  const counts: Record<string, number> = {
    critical: summary.critical_count,
    high: summary.high_count,
    medium: summary.medium_count,
    low: summary.low_count,
    info: summary.info_count,
  };

  const total = summary.total_alerts;

  return (
    <div className="panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header" style={{ borderBottom: 'none', paddingBottom: 0 }}>
        <span className="panel-title">SEVERITY DISTRIBUTION</span>
      </div>
      <div className="panel-content" style={{ flex: 1, padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: '14px', marginTop: 'var(--space-2)' }}>
        {total === 0 ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '13px', fontWeight: 500, letterSpacing: '0.05em' }}>NO ALERTS</span>
            <span style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '6px' }}>Severity data unavailable.</span>
          </div>
        ) : (
          SEVERITY_ORDER.filter(s => s !== 'info').map((sev) => {
            const count = counts[sev] || 0;
            const pct = total > 0 ? Math.round((count / total) * 100) : 0;
            const isActive = count > 0;

            return (
              <div key={sev} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                {/* Fixed width for alignment */}
                <div style={{ width: '64px', display: 'flex', justifyContent: 'flex-start' }}>
                  <span className={`severity-badge ${sev}`} style={{ opacity: isActive ? 1 : 0.4 }}>
                    {sev.toUpperCase()}
                  </span>
                </div>
                
                {/* Bar Track & Fill */}
                <div style={{ flex: 1, height: '4px', backgroundColor: 'var(--bg-panel-dark)', borderRadius: '2px', overflow: 'hidden', position: 'relative' }}>
                  <div style={{ 
                    position: 'absolute',
                    top: 0, left: 0, bottom: 0,
                    width: `${pct}%`, 
                    backgroundColor: severityColor(sev),
                    transition: 'width 0.5s cubic-bezier(0.16, 1, 0.3, 1)',
                    boxShadow: isActive ? `0 0 8px ${severityColor(sev)}40` : 'none'
                  }} />
                </div>

                {/* Numbers */}
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', width: '60px', justifyContent: 'flex-end' }}>
                  <span className="mono" style={{ fontSize: '12px', color: isActive ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                    {count}
                  </span>
                  <span className="mono" style={{ fontSize: '10px', color: 'var(--text-muted)', width: '28px', textAlign: 'right' }}>
                    {pct}%
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
