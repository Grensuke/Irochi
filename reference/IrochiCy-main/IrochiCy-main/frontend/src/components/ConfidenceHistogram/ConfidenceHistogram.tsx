import { useState } from 'react';
import type { ConfidenceBucket } from '@/types';

interface ConfidenceHistogramProps { buckets: ConfidenceBucket[]; color: string; }

export default function ConfidenceHistogram({ buckets, color }: ConfidenceHistogramProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const maxCount = Math.max(...buckets.map(b => b.count), 1);
  const chartW = 600, chartH = 200, barW = 48, gap = 12, padL = 40, padB = 30;

  return (
    <svg width="100%" viewBox={`0 0 ${chartW} ${chartH + padB}`} style={{ display: 'block' }}>
      {/* Y-axis labels */}
      {[0, 0.25, 0.5, 0.75, 1].map(frac => {
        const y = chartH - frac * chartH;
        const val = Math.round(frac * maxCount);
        return (
          <g key={frac}>
            <line x1={padL} y1={y} x2={chartW} y2={y} stroke="var(--border-subtle)" strokeWidth="0.5" />
            <text x={padL - 6} y={y + 4} textAnchor="end" fill="var(--text-tertiary)" fontSize="10" fontFamily="'IBM Plex Mono', monospace">{val}</text>
          </g>
        );
      })}
      {/* Bars */}
      {buckets.map((b, i) => {
        const barH = (b.count / maxCount) * chartH;
        const x = padL + i * (barW + gap);
        const y = chartH - barH;
        const isHovered = hoveredIdx === i;
        return (
          <g key={i} onMouseEnter={() => setHoveredIdx(i)} onMouseLeave={() => setHoveredIdx(null)} style={{ cursor: 'pointer' }}>
            <rect x={x} y={y} width={barW} height={barH} rx={3} ry={3}
              fill={color} opacity={isHovered ? 0.9 : 0.7}
              style={{ transition: 'opacity 150ms ease' }} />
            {/* X-axis label */}
            <text x={x + barW / 2} y={chartH + 14} textAnchor="middle" fill="var(--text-tertiary)" fontSize="9" fontFamily="'IBM Plex Mono', monospace">{b.range}</text>
            {/* Tooltip */}
            {isHovered && (
              <g>
                <rect x={x + barW / 2 - 24} y={y - 24} width={48} height={20} rx={4} fill="var(--bg-elevated)" stroke="var(--border-default)" strokeWidth="0.5" />
                <text x={x + barW / 2} y={y - 10} textAnchor="middle" fill="var(--text-primary)" fontSize="11" fontFamily="'IBM Plex Mono', monospace" fontWeight="600">{b.count}</text>
              </g>
            )}
          </g>
        );
      })}
    </svg>
  );
}
