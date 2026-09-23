import { useMemo } from 'react';
import type { ProtocolBreakdown } from '@/types';
import './ProtocolDonut.css';

interface ProtocolDonutProps {
  data: ProtocolBreakdown[];
}

const PROTOCOL_HEX: Record<string, string> = {
  TCP: '#00C2A8',
  UDP: '#FF7A2F',
  ICMP: '#A78BFA',
  Other: '#505A68',
};

const SIZE = 160;
const RADIUS = 60;
const INNER_RADIUS = 40;
const CENTER = SIZE / 2;

export default function ProtocolDonut({ data }: ProtocolDonutProps) {
  const total = useMemo(() => data.reduce((sum, d) => sum + d.count, 0), [data]);

  const arcs = useMemo(() => {
    let cumAngle = -Math.PI / 2; // Start from top
    return data.map(d => {
      const angle = (d.percentage / 100) * Math.PI * 2;
      const startAngle = cumAngle;
      const endAngle = cumAngle + angle;
      cumAngle = endAngle;

      const gap = 0.02; // Small gap between segments

      const x1Outer = CENTER + RADIUS * Math.cos(startAngle + gap);
      const y1Outer = CENTER + RADIUS * Math.sin(startAngle + gap);
      const x2Outer = CENTER + RADIUS * Math.cos(endAngle - gap);
      const y2Outer = CENTER + RADIUS * Math.sin(endAngle - gap);

      const x1Inner = CENTER + INNER_RADIUS * Math.cos(endAngle - gap);
      const y1Inner = CENTER + INNER_RADIUS * Math.sin(endAngle - gap);
      const x2Inner = CENTER + INNER_RADIUS * Math.cos(startAngle + gap);
      const y2Inner = CENTER + INNER_RADIUS * Math.sin(startAngle + gap);

      const largeArc = angle > Math.PI ? 1 : 0;

      const path = [
        `M ${x1Outer},${y1Outer}`,
        `A ${RADIUS},${RADIUS} 0 ${largeArc} 1 ${x2Outer},${y2Outer}`,
        `L ${x1Inner},${y1Inner}`,
        `A ${INNER_RADIUS},${INNER_RADIUS} 0 ${largeArc} 0 ${x2Inner},${y2Inner}`,
        'Z',
      ].join(' ');

      return {
        path,
        color: PROTOCOL_HEX[d.protocol] || '#505A68',
        protocol: d.protocol,
      };
    });
  }, [data]);

  const formatTotal = (n: number): string => {
    if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
    return n.toLocaleString();
  };

  return (
    <div className="protocol-donut">
      <div className="protocol-donut__title">PROTOCOL BREAKDOWN</div>
      <div className="protocol-donut__chart">
        <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`}>
          {arcs.map(arc => (
            <path
              key={arc.protocol}
              d={arc.path}
              fill={arc.color}
              opacity={0.85}
            />
          ))}
          {/* Center text */}
          <text
            x={CENTER}
            y={CENTER - 4}
            textAnchor="middle"
            className="protocol-donut__center-text"
            fontSize="18"
          >
            {formatTotal(total)}
          </text>
          <text
            x={CENTER}
            y={CENTER + 12}
            textAnchor="middle"
            className="protocol-donut__center-label"
          >
            EVENTS
          </text>
        </svg>
      </div>
      <div className="protocol-donut__legend">
        {data.map(d => (
          <div key={d.protocol} className="protocol-donut__legend-row">
            <span
              className="protocol-donut__legend-dot"
              style={{ backgroundColor: PROTOCOL_HEX[d.protocol] || '#505A68' }}
            />
            <span className="protocol-donut__legend-label">{d.protocol}</span>
            <span className="protocol-donut__legend-pct">{d.percentage}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
