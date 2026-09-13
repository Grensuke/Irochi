import { useMemo } from 'react';
import type { Alert } from '../types';

interface TopSourcesProps {
  alerts: Alert[];
}

export function TopSources({ alerts }: TopSourcesProps) {
  const { topSources, maxCount } = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const a of alerts) {
      const src = a.src_ip || a.evidence?.src_ip;
      if (src) {
        counts[src] = (counts[src] || 0) + 1;
      }
    }
    const sorted = Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);
      
    const max = sorted.length > 0 ? sorted[0][1] : 0;
    return { topSources: sorted, maxCount: max };
  }, [alerts]);

  return (
    <div className="panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header" style={{ borderBottom: 'none', paddingBottom: 0 }}>
        <span className="panel-title">TOP SOURCES</span>
      </div>
      <div className="panel-content" style={{ flex: 1, padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: '12px', marginTop: 'var(--space-2)' }}>
        {topSources.length === 0 ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '13px', fontWeight: 500, letterSpacing: '0.05em' }}>NO ALERTS</span>
            <span style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '6px' }}>Source data unavailable.</span>
          </div>
        ) : (
          topSources.map(([ip, count]) => {
            const pct = maxCount > 0 ? (count / maxCount) * 100 : 0;
            return (
              <div key={ip} style={{ position: 'relative', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0' }}>
                {/* Subtle Background Bar */}
                <div style={{ 
                  position: 'absolute', 
                  top: 0, left: 0, bottom: 0, 
                  width: `${pct}%`, 
                  backgroundColor: 'var(--bg-panel-dark)', 
                  borderRadius: '2px',
                  zIndex: 0,
                  transition: 'width 0.5s cubic-bezier(0.16, 1, 0.3, 1)'
                }} />
                
                <span className="mono" style={{ fontSize: '12px', color: 'var(--text-primary)', zIndex: 1, paddingLeft: '6px' }}>{ip}</span>
                <span className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)', zIndex: 1, paddingRight: '6px' }}>{count}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
