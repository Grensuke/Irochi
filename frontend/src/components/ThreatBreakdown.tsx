import { useMemo, useState } from 'react';
import type { DashboardSummary, ThreatType } from '../types';
import { threatLabel, threatColor } from '../utils/format';

interface ThreatBreakdownProps {
  summary: DashboardSummary | null;
  loading: boolean;
}

export function ThreatBreakdown({ summary, loading }: ThreatBreakdownProps) {
  const [hoveredType, setHoveredType] = useState<ThreatType | null>(null);

  const chartData = useMemo(() => {
    if (!summary || !summary.by_threat_type) return [];
    
    const items = Object.entries(summary.by_threat_type)
      .map(([type, count]) => ({
        type: type as ThreatType,
        count,
      }))
      .sort((a, b) => b.count - a.count);

    return items;
  }, [summary]);

  if (loading || !summary) {
    return (
      <div className="panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <div className="panel-header" style={{ borderBottom: 'none' }}>
          <span className="panel-title">THREAT DISTRIBUTION</span>
        </div>
        <div className="panel-content" style={{ flex: 1, padding: 'var(--space-4)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ color: 'var(--text-muted)' }}>Loading...</span>
        </div>
      </div>
    );
  }

  const total = summary.total_alerts;

  // Calculate donut segments
  const size = 160;
  const cx = size / 2;
  const cy = size / 2;
  const strokeWidth = 20; // slightly thinner for premium feel
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  
  let currentOffset = 0;
  
  const segments = chartData.map(item => {
    const fraction = total > 0 ? item.count / total : 0;
    // Add small gap by reducing the fraction slightly for the dasharray, only if not 100%
    const gap = fraction > 0 && fraction < 1 ? 2 : 0;
    const dash = Math.max(0, (fraction * circumference) - gap);
    const emptySpace = circumference - dash;
    const strokeDasharray = `${dash} ${emptySpace}`;
    const strokeDashoffset = circumference - currentOffset;
    currentOffset += fraction * circumference;
    
    return {
      ...item,
      fraction,
      strokeDasharray,
      strokeDashoffset
    };
  });

  return (
    <div className="panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header" style={{ borderBottom: 'none', paddingBottom: 0 }}>
        <span className="panel-title">THREAT DISTRIBUTION</span>
      </div>
      <div className="panel-content" style={{ flex: 1, padding: 'var(--space-3) var(--space-4)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        {total === 0 ? (
          <div style={{ flex: 1, textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '13px', fontWeight: 500, letterSpacing: '0.05em' }}>NO ALERTS</span>
            <span style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '6px' }}>Distribution unavailable.</span>
          </div>
        ) : (
          <>
            {/* Donut SVG */}
            <div 
              style={{ position: 'relative', width: size, height: size }}
              onMouseLeave={() => setHoveredType(null)}
            >
              <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ overflow: 'visible' }}>
                {/* Background track */}
                <circle
                  cx={cx}
                  cy={cy}
                  r={radius}
                  fill="transparent"
                  stroke="var(--bg-panel-dark)"
                  strokeWidth={strokeWidth}
                />
                
                {segments.map((seg) => {
                  const isHovered = hoveredType === seg.type;
                  const isOtherHovered = hoveredType !== null && !isHovered;
                  
                  return (
                    <circle
                      key={seg.type}
                      cx={cx}
                      cy={cy}
                      r={radius}
                      fill="transparent"
                      stroke={threatColor(seg.type)}
                      strokeWidth={isHovered ? strokeWidth + 4 : strokeWidth}
                      strokeDasharray={seg.strokeDasharray}
                      strokeDashoffset={seg.strokeDashoffset}
                      transform={`rotate(-90 ${cx} ${cy})`}
                      opacity={isOtherHovered ? 0.2 : 1}
                      style={{ 
                        transition: 'opacity 0.3s ease, stroke-width 0.3s ease, stroke-dasharray 0.5s ease',
                        cursor: 'pointer',
                        strokeLinecap: 'butt'
                      }}
                      onMouseEnter={() => setHoveredType(seg.type)}
                    />
                  );
                })}
              </svg>
              {/* Center Text */}
              <div style={{ 
                position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, 
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                pointerEvents: 'none'
              }}>
                <span style={{ fontSize: '26px', fontWeight: 300, color: 'var(--text-primary)', lineHeight: 1, letterSpacing: '-0.02em' }}>{total}</span>
                <span style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase', marginTop: '4px', letterSpacing: '0.1em' }}>TOTAL ALERTS</span>
              </div>
            </div>

            {/* Legend */}
            <div style={{ flex: 1, marginLeft: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {segments.map(seg => {
                const pct = Math.round(seg.fraction * 100);
                const isHovered = hoveredType === seg.type;
                const isOtherHovered = hoveredType !== null && !isHovered;
                
                return (
                  <div 
                    key={seg.type} 
                    style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'space-between',
                      opacity: isOtherHovered ? 0.4 : 1,
                      transition: 'opacity 0.3s ease'
                    }}
                    onMouseEnter={() => setHoveredType(seg.type)}
                    onMouseLeave={() => setHoveredType(null)}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ 
                        width: '6px', 
                        height: '6px', 
                        borderRadius: '50%', 
                        backgroundColor: threatColor(seg.type),
                        transform: isHovered ? 'scale(1.5)' : 'scale(1)',
                        transition: 'transform 0.2s ease'
                      }} />
                      <span style={{ fontSize: '12px', color: isHovered ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                        {threatLabel(seg.type)}
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span className="mono" style={{ fontSize: '12px', color: 'var(--text-primary)' }}>{seg.count}</span>
                      <span className="mono" style={{ fontSize: '12px', color: 'var(--text-muted)', width: '32px', textAlign: 'right' }}>{pct}%</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
