import { useState, useMemo } from 'react';
import type { TimelineBucket, ThreatType } from '@/types';
import './ThreatTimeline.css';

interface ThreatTimelineProps {
  data: TimelineBucket[];
}

const THREAT_KEYS: ThreatType[] = ['ddos', 'recon', 'dns', 'tls', 'exfil'];
const THREAT_COLORS: Record<ThreatType, string> = {
  ddos: 'var(--threat-ddos)',
  recon: 'var(--threat-recon)',
  dns: 'var(--threat-dns)',
  tls: 'var(--threat-tls)',
  exfil: 'var(--threat-exfil)',
};
const THREAT_LABELS: Record<ThreatType, string> = {
  ddos: 'DDoS',
  recon: 'Recon',
  dns: 'DNS-DGA',
  tls: 'TLS-C2',
  exfil: 'Exfil',
};

// CSS custom property -> resolved color (fallback hex for SVG)
const THREAT_HEX: Record<ThreatType, string> = {
  ddos: '#FF3B5C',
  recon: '#FF7A2F',
  dns: '#A78BFA',
  tls: '#5B8CFF',
  exfil: '#F5C518',
};

const CHART_WIDTH = 720;
const CHART_HEIGHT = 200;
const PADDING = { top: 20, right: 20, bottom: 35, left: 45 };

export default function ThreatTimeline({ data }: ThreatTimelineProps) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const { maxY, plotW, plotH, xStep } = useMemo(() => {
    const maxStack = data.reduce((max, bucket) => {
      const total = THREAT_KEYS.reduce((sum, key) => sum + bucket[key], 0);
      return Math.max(max, total);
    }, 0);
    const plotW = CHART_WIDTH - PADDING.left - PADDING.right;
    const plotH = CHART_HEIGHT - PADDING.top - PADDING.bottom;
    const xStep = data.length > 1 ? plotW / (data.length - 1) : plotW;
    return { maxY: maxStack || 1, plotW, plotH, xStep };
  }, [data]);

  // Build stacked area paths
  const areaPaths = useMemo(() => {
    const paths: { key: ThreatType; d: string; lineD: string }[] = [];

    // Calculate cumulative sums for stacking
    const cumulative = data.map(bucket => {
      const result: Record<ThreatType, number> = {} as Record<ThreatType, number>;
      let sum = 0;
      for (const key of THREAT_KEYS) {
        sum += bucket[key];
        result[key] = sum;
      }
      return result;
    });

    for (let ti = THREAT_KEYS.length - 1; ti >= 0; ti--) {
      const key = THREAT_KEYS[ti];
      const topPoints = data.map((_, i) => {
        const x = PADDING.left + i * xStep;
        const y = PADDING.top + plotH - (cumulative[i][key] / maxY) * plotH;
        return { x, y };
      });

      const bottomPoints = data.map((_, i) => {
        const x = PADDING.left + i * xStep;
        const prevKey = ti > 0 ? THREAT_KEYS[ti - 1] : null;
        const y = prevKey
          ? PADDING.top + plotH - (cumulative[i][prevKey] / maxY) * plotH
          : PADDING.top + plotH;
        return { x, y };
      });

      // Smooth area path
      let d = `M ${topPoints[0].x},${topPoints[0].y}`;
      for (let i = 1; i < topPoints.length; i++) {
        d += ` L ${topPoints[i].x},${topPoints[i].y}`;
      }
      for (let i = bottomPoints.length - 1; i >= 0; i--) {
        d += ` L ${bottomPoints[i].x},${bottomPoints[i].y}`;
      }
      d += ' Z';

      // Line path (top edge only)
      let lineD = `M ${topPoints[0].x},${topPoints[0].y}`;
      for (let i = 1; i < topPoints.length; i++) {
        lineD += ` L ${topPoints[i].x},${topPoints[i].y}`;
      }

      paths.push({ key, d, lineD });
    }

    return paths;
  }, [data, maxY, plotH, xStep]);

  // Y-axis ticks
  const yTicks = useMemo(() => {
    const tickCount = 5;
    const ticks: { value: number; y: number }[] = [];
    for (let i = 0; i <= tickCount; i++) {
      const value = Math.round((maxY / tickCount) * i);
      const y = PADDING.top + plotH - (value / maxY) * plotH;
      ticks.push({ value, y });
    }
    return ticks;
  }, [maxY, plotH]);

  // Tooltip data
  const tooltipData = useMemo(() => {
    if (hoverIndex === null || !data[hoverIndex]) return null;
    const bucket = data[hoverIndex];
    return {
      hour: bucket.hour,
      items: THREAT_KEYS.map(key => ({
        key,
        label: THREAT_LABELS[key],
        value: bucket[key],
        color: THREAT_HEX[key],
      })),
      total: THREAT_KEYS.reduce((sum, key) => sum + bucket[key], 0),
    };
  }, [hoverIndex, data]);

  return (
    <div className="threat-timeline">
      <div className="threat-timeline__title">THREAT ACTIVITY — 24H</div>
      <div className="threat-timeline__chart" style={{ position: 'relative' }}>
        <svg
          viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
          style={{ width: '100%', height: 'auto' }}
          onMouseLeave={() => setHoverIndex(null)}
        >
          {/* Y-axis grid lines */}
          {yTicks.map(tick => (
            <g key={tick.value}>
              <line
                x1={PADDING.left}
                y1={tick.y}
                x2={PADDING.left + plotW}
                y2={tick.y}
                stroke="var(--border-subtle)"
                strokeWidth="0.5"
                strokeDasharray="3,3"
              />
              <text
                x={PADDING.left - 8}
                y={tick.y + 3}
                textAnchor="end"
                fill="var(--text-tertiary)"
                fontFamily="'IBM Plex Mono', monospace"
                fontSize="10"
              >
                {tick.value}
              </text>
            </g>
          ))}

          {/* Stacked areas */}
          {areaPaths.map(({ key, d, lineD }) => (
            <g key={key}>
              <path d={d} fill={THREAT_HEX[key]} opacity={0.2} />
              <path d={lineD} fill="none" stroke={THREAT_HEX[key]} strokeWidth="1.5" />
            </g>
          ))}

          {/* X-axis labels */}
          {data.map((bucket, i) => {
            // Show every 3rd label to avoid crowding
            if (i % 3 !== 0 && i !== data.length - 1) return null;
            const x = PADDING.left + i * xStep;
            return (
              <text
                key={i}
                x={x}
                y={CHART_HEIGHT - 5}
                textAnchor="middle"
                fill="var(--text-tertiary)"
                fontFamily="'IBM Plex Mono', monospace"
                fontSize="10"
              >
                {bucket.hour}
              </text>
            );
          })}

          {/* Hover interaction zones */}
          {data.map((_, i) => {
            const x = PADDING.left + i * xStep - xStep / 2;
            return (
              <rect
                key={i}
                x={Math.max(PADDING.left, x)}
                y={PADDING.top}
                width={xStep}
                height={plotH}
                fill="transparent"
                onMouseEnter={() => setHoverIndex(i)}
              />
            );
          })}

          {/* Crosshair */}
          {hoverIndex !== null && (
            <line
              x1={PADDING.left + hoverIndex * xStep}
              y1={PADDING.top}
              x2={PADDING.left + hoverIndex * xStep}
              y2={PADDING.top + plotH}
              stroke="var(--text-tertiary)"
              strokeWidth="1"
              strokeDasharray="4,4"
              opacity={0.6}
            />
          )}
        </svg>

        {/* Tooltip */}
        {tooltipData && hoverIndex !== null && (
          <div
            className="threat-timeline__tooltip"
            style={{
              left: `${((PADDING.left + hoverIndex * xStep) / CHART_WIDTH) * 100}%`,
              top: '10px',
              transform: hoverIndex > data.length / 2 ? 'translateX(-110%)' : 'translateX(10%)',
            }}
          >
            <div style={{ fontWeight: 600, marginBottom: '4px' }}>{tooltipData.hour}</div>
            {tooltipData.items.map(item => (
              <div key={item.key} className="threat-timeline__tooltip-row">
                <span className="threat-timeline__tooltip-dot" style={{ backgroundColor: item.color }} />
                <span>{item.label}:</span>
                <span style={{ fontWeight: 500 }}>{item.value}</span>
              </div>
            ))}
            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '3px', marginTop: '3px', fontWeight: 600 }}>
              Total: {tooltipData.total}
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="threat-timeline__legend">
        {THREAT_KEYS.map(key => (
          <div key={key} className="threat-timeline__legend-item">
            <span className="threat-timeline__legend-dot" style={{ backgroundColor: THREAT_HEX[key] }} />
            {THREAT_LABELS[key]}
          </div>
        ))}
      </div>
    </div>
  );
}
