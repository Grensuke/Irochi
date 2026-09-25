import { useMemo, useState } from 'react';
import type { Alert, ThreatType } from '../types';
import { THREAT_TYPE_LABELS } from '../types';
import { threatLabel, threatColor } from '../utils/format';
import './ThreatTimeline.css';

interface ThreatTimelineProps {
  alerts: Alert[];
}

export function ThreatTimeline({ alerts }: ThreatTimelineProps) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const [windowHours, setWindowHours] = useState<number>(1);

  const { buckets, activeThreats, maxCount, binDurationMs } = useMemo(() => {
    const bins: Record<string, number>[] = Array.from({ length: 24 }, () => ({}));
    const threatSet = new Set<string>();

    const binDurationMs = (windowHours * 60 * 60 * 1000) / 24;

    alerts.forEach((alert) => {
      const detectedTime = alert.detected_at ? new Date(alert.detected_at).getTime() : Date.now();
      const now = Date.now();
      const ageMs = now - detectedTime;

      let binIndex = 23 - Math.floor(ageMs / binDurationMs);

      // Clamp to bounds. If older than selected window, we drop it from this chart
      if (binIndex < 0) return;
      if (binIndex > 23) binIndex = 23;
      
      const type = alert.threat_type;
      threatSet.add(type);
      bins[binIndex][type] = (bins[binIndex][type] || 0) + 1;
    });

    const active = Array.from(threatSet) as ThreatType[];
    // Order threats deterministically
    active.sort();
    
    let max = 0;
    // Calculate max individual threat count or max total count?
    // The prompt says multi-series, not necessarily stacked area. Overlapping lines.
    // So max is the max of any single threat in any bin.
    bins.forEach(bin => {
      active.forEach(t => {
        if ((bin[t] || 0) > max) max = bin[t] || 0;
      });
    });

    // Ensure we have at least 10 for Y axis scale
    max = Math.max(max, 10);
    // Round up max to nearest 5
    max = Math.ceil(max / 5) * 5;

    return { buckets: bins, activeThreats: active, maxCount: max, binDurationMs };
  }, [alerts, windowHours]);

  const W = 700;
  const H = 220;
  const paddingY = 40;
  const paddingX = 40;
  const usableW = W - paddingX * 2;
  const usableH = H - paddingY * 2;

  const getX = (i: number) => paddingX + (i / 23) * usableW;
  const getY = (val: number) => (H - paddingY) - (val / maxCount) * usableH;

  // Calculate paths
  const seriesPaths: { type: string, line: string, area: string, color: string }[] = [];
  
  if (activeThreats.length > 0) {
    activeThreats.forEach((threat) => {
      let dLine = '';
      let dArea = '';
      buckets.forEach((bin, i) => {
        const val = bin[threat] || 0;
        const x = getX(i);
        const y = getY(val);
        
        if (i === 0) {
          dLine += `M ${x},${y} `;
          dArea += `M ${x},${getY(0)} L ${x},${y} `;
        } else {
          // Smooth curve using bezier or just simple line? Prompt: "slightly rounded paths" -> "strokeLinejoin=round" is usually enough, but we can do a simple catmull-rom or just straight lines with round joins. Let's use straight lines with strokeLinejoin="round" for crispness.
          dLine += `L ${x},${y} `;
          dArea += `L ${x},${y} `;
        }
      });
      // Close area
      dArea += `L ${getX(23)},${getY(0)} Z`;

      seriesPaths.push({
        type: threat,
        line: dLine,
        area: dArea,
        color: threatColor(threat)
      });
    });
  }

  // Hover Tooltip
  let tooltipData = null;
  if (hoverIndex !== null && hoverIndex >= 0 && hoverIndex < 24) {
    const bin = buckets[hoverIndex];
    const total = activeThreats.reduce((sum, t) => sum + (bin[t] || 0), 0);
    const hourLabel = new Date(Date.now() - (23 - hoverIndex) * binDurationMs).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' UTC';
    
    // Sort tooltip items by count desc
    const sortedActive = [...activeThreats].sort((a, b) => (bin[b] || 0) - (bin[a] || 0));

    tooltipData = {
      x: getX(hoverIndex),
      hourLabel,
      bin,
      total,
      sortedActive
    };
  }

  return (
    <div className="panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header" style={{ borderBottom: 'none', paddingBottom: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <span className="panel-title">OBSERVED ALERT ACTIVITY</span>
          <select 
            value={windowHours} 
            onChange={(e) => setWindowHours(Number(e.target.value))}
            style={{
              background: 'transparent',
              border: '1px solid var(--border-color)',
              color: 'var(--text-secondary)',
              fontSize: '11px',
              padding: '2px 6px',
              borderRadius: '4px',
              outline: 'none',
              cursor: 'pointer'
            }}
          >
            <option value={1}>LAST 1H</option>
            <option value={3}>LAST 3H</option>
            <option value={12}>LAST 12H</option>
            <option value={24}>LAST 24H</option>
          </select>
        </div>
        
        {/* Premium Legend */}
        {activeThreats.length > 0 && (
          <div style={{ display: 'flex', gap: 'var(--space-4)', marginTop: 'var(--space-2)' }}>
            {activeThreats.map(t => (
              <div key={t} style={{ display: 'flex', alignItems: 'center', gap: '6px' }} className="timeline-legend-item">
                <span style={{ width: '6px', height: '6px', backgroundColor: threatColor(t), borderRadius: '50%' }} />
                <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{threatLabel(t)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <div className="panel-content" style={{ flex: 1, position: 'relative', marginTop: 'var(--space-2)' }}>
        {alerts.length === 0 ? (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '13px', fontWeight: 500, letterSpacing: '0.05em' }}>NO ALERT ACTIVITY</span>
            <span style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '6px' }}>No observed alerts in the selected {windowHours}-hour window.</span>
          </div>
        ) : (
          <svg 
            width="100%" 
            height="100%" 
            viewBox={`0 0 ${W} ${H}`} 
            preserveAspectRatio="none"
            onMouseLeave={() => setHoverIndex(null)}
            onMouseMove={(e) => {
              const rect = e.currentTarget.getBoundingClientRect();
              const xPercent = (e.clientX - rect.left) / rect.width;
              let i = Math.round(xPercent * 23);
              if (i < 0) i = 0;
              if (i > 23) i = 23;
              setHoverIndex(i);
            }}
            className="threat-timeline-svg"
          >
            {/* Gradients */}
            <defs>
              {activeThreats.map(t => (
                <linearGradient key={`grad-${t}`} id={`grad-${t}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={threatColor(t)} stopOpacity="0.15" />
                  <stop offset="100%" stopColor={threatColor(t)} stopOpacity="0.0" />
                </linearGradient>
              ))}
            </defs>

            {/* Grid lines - very subtle */}
            <line x1={paddingX} y1={getY(maxCount)} x2={W - paddingX} y2={getY(maxCount)} stroke="var(--border-color)" strokeWidth="1" opacity="0.4" strokeDasharray="2 4" />
            <line x1={paddingX} y1={getY(maxCount / 2)} x2={W - paddingX} y2={getY(maxCount / 2)} stroke="var(--border-color)" strokeWidth="1" opacity="0.4" strokeDasharray="2 4" />
            <line x1={paddingX} y1={getY(0)} x2={W - paddingX} y2={getY(0)} stroke="var(--border-color)" strokeWidth="1" opacity="0.8" />

            {/* Y-axis labels */}
            <text x={paddingX - 12} y={getY(maxCount) + 3} fill="var(--text-muted)" fontSize="10" textAnchor="end">{maxCount}</text>
            <text x={paddingX - 12} y={getY(maxCount / 2) + 3} fill="var(--text-muted)" fontSize="10" textAnchor="end">{maxCount / 2}</text>
            <text x={paddingX - 12} y={getY(0) + 3} fill="var(--text-muted)" fontSize="10" textAnchor="end">0</text>

            {/* X-axis labels */}
            <text x={getX(0)} y={H - paddingY + 20} fill="var(--text-muted)" fontSize="10" textAnchor="middle">{windowHours < 1 ? `-${windowHours * 60}m` : `-${windowHours}h`}</text>
            <text x={getX(12)} y={H - paddingY + 20} fill="var(--text-muted)" fontSize="10" textAnchor="middle">{windowHours / 2 < 1 ? `-${(windowHours / 2) * 60}m` : `-${windowHours / 2}h`}</text>
            <text x={getX(23)} y={H - paddingY + 20} fill="var(--text-muted)" fontSize="10" textAnchor="middle">Now</text>

            {/* Series Lines & Areas */}
            {seriesPaths.map((series) => (
              <g key={series.type} className={`series-group ${hoverIndex !== null ? 'has-hover' : ''}`}>
                <path
                  d={series.area}
                  fill={`url(#grad-${series.type})`}
                  className="series-area"
                />
                <path
                  d={series.line}
                  fill="none"
                  stroke={series.color}
                  strokeWidth="1.5"
                  strokeLinejoin="round"
                  strokeLinecap="round"
                  className="series-line"
                />
              </g>
            ))}

            {/* Hover Tooltip Overlay */}
            {tooltipData && (
              <g className="hover-overlay">
                {/* Vertical Guide Line */}
                <line 
                  x1={tooltipData.x} 
                  y1={paddingY - 10} 
                  x2={tooltipData.x} 
                  y2={H - paddingY} 
                  stroke="var(--text-muted)" 
                  strokeWidth="1" 
                  opacity="0.5"
                  strokeDasharray="2 2" 
                />
                
                <circle cx={tooltipData.x} cy={getY(0)} r="2.5" fill="var(--text-muted)" />
                
                {/* Emphasized Points */}
                {activeThreats.map(t => (
                  <circle 
                    key={`pt-${t}`}
                    cx={tooltipData.x} 
                    cy={getY(tooltipData.bin[t] || 0)} 
                    r="3.5" 
                    fill="var(--bg-primary)" 
                    stroke={threatColor(t)} 
                    strokeWidth="2" 
                    className="hover-point"
                  />
                ))}

                {/* Tooltip Panel */}
                {(() => {
                  const boxWidth = 160;
                  const rowHeight = 18;
                  const boxHeight = 45 + tooltipData.sortedActive.length * rowHeight;
                  const isRightHalf = hoverIndex !== null && hoverIndex > 12;
                  const boxX = isRightHalf ? tooltipData.x - boxWidth - 15 : tooltipData.x + 15;
                  
                  // Keep box inside SVG bounds vertically
                  let boxY = Math.max(paddingY - 10, Math.min(getY(tooltipData.total / 2) - boxHeight / 2, H - paddingY - boxHeight + 10));
                  if (boxY < 10) boxY = 10;

                  return (
                    <g transform={`translate(${boxX}, ${boxY})`} className="tooltip-panel">
                      {/* Premium shadow */}
                      <rect width={boxWidth} height={boxHeight} rx="4" fill="#000" opacity="0.2" transform="translate(0, 4)" filter="blur(4px)" />
                      <rect width={boxWidth} height={boxHeight} rx="4" fill="var(--bg-primary)" stroke="var(--border-color)" strokeWidth="1" />
                      
                      <text x="12" y="22" fill="var(--text-primary)" fontSize="11" fontWeight="600" letterSpacing="0.05em">{tooltipData.hourLabel}</text>
                      
                      <line x1="0" y1="32" x2={boxWidth} y2="32" stroke="var(--border-color)" opacity="0.5" />

                      {tooltipData.sortedActive.map((t, i) => (
                        <g key={`tt-${t}`} transform={`translate(12, ${46 + i * rowHeight})`}>
                          <circle cx="3" cy="-3" r="3" fill={threatColor(t)} />
                          <text x="12" y="0" fill={tooltipData.bin[t] ? 'var(--text-secondary)' : 'var(--text-muted)'} fontSize="11">{THREAT_TYPE_LABELS[t] || t}</text>
                          <text x={boxWidth - 24} y="0" fill={tooltipData.bin[t] ? 'var(--text-primary)' : 'var(--text-muted)'} fontSize="11" textAnchor="end" className="mono">{tooltipData.bin[t] || 0}</text>
                        </g>
                      ))}
                      
                      <line x1="12" y1={46 + tooltipData.sortedActive.length * rowHeight - 6} x2={boxWidth - 12} y2={46 + tooltipData.sortedActive.length * rowHeight - 6} stroke="var(--border-color)" opacity="0.5" />
                      
                      <text x="12" y={46 + tooltipData.sortedActive.length * rowHeight + 10} fill="var(--text-primary)" fontSize="11" fontWeight="600">Total</text>
                      <text x={boxWidth - 24} y={46 + tooltipData.sortedActive.length * rowHeight + 10} fill="var(--text-primary)" fontSize="11" fontWeight="600" textAnchor="end" className="mono">{tooltipData.total}</text>
                    </g>
                  );
                })()}
              </g>
            )}
          </svg>
        )}
      </div>
    </div>
  );
}
