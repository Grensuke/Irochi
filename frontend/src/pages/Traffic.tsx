/**
 * Traffic Monitor page.
 *
 * Visualises observed passive traffic throughput and protocol distribution
 * using native SVG charts (no external chart library).
 *
 * All data is MOCK/DEMO — not real production throughput.
 */

import { MOCK_TRAFFIC_TIMESERIES, MOCK_PROTOCOL_DIST } from '../services/mockData';
import { formatRate } from '../utils/format';

const W = 600;
const H = 120;
const PAD = { top: 8, right: 16, bottom: 24, left: 56 };

function TrafficChart() {
  const data = MOCK_TRAFFIC_TIMESERIES;
  const maxBps = Math.max(...data.map((d) => d.bps));

  const scaleX = (i: number) =>
    PAD.left + (i / (data.length - 1)) * (W - PAD.left - PAD.right);
  const scaleY = (v: number) =>
    PAD.top + (1 - v / maxBps) * (H - PAD.top - PAD.bottom);

  const points = data.map((d, i) => `${scaleX(i)},${scaleY(d.bps)}`).join(' ');
  const areaPoints = [
    `${scaleX(0)},${H - PAD.bottom}`,
    ...data.map((d, i) => `${scaleX(i)},${scaleY(d.bps)}`),
    `${scaleX(data.length - 1)},${H - PAD.bottom}`,
  ].join(' ');

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      height={H}
      role="img"
      aria-label="Observed traffic throughput over time (demo data)"
    >
      {/* Y-axis labels */}
      {[0, 0.5, 1].map((t) => {
        const y = scaleY(maxBps * t);
        return (
          <text key={t} x={PAD.left - 6} y={y + 4} textAnchor="end" fontSize="9" fill="var(--text-muted)">
            {formatRate(maxBps * t)}
          </text>
        );
      })}

      {/* Horizontal grid lines */}
      {[0.5, 1].map((t) => (
        <line
          key={t}
          x1={PAD.left}
          y1={scaleY(maxBps * t)}
          x2={W - PAD.right}
          y2={scaleY(maxBps * t)}
          stroke="var(--border-subtle)"
          strokeDasharray="3,3"
        />
      ))}

      {/* Area fill */}
      <polygon
        points={areaPoints}
        fill="var(--accent-primary)"
        fillOpacity="0.08"
      />

      {/* Base Static Line */}
      <polyline
        points={points}
        fill="none"
        stroke="var(--accent-primary)"
        strokeWidth="1.5"
        strokeLinejoin="round"
        opacity="0.6"
      />

      {/* Flow Motion Overlay Line */}
      <polyline
        className="chart-flow-line"
        points={points}
        fill="none"
        stroke="var(--accent-cyan)"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />

      {/* X-axis labels (every other tick) */}
      {data.map((d, i) =>
        i % 2 === 0 ? (
          <text
            key={i}
            x={scaleX(i)}
            y={H - PAD.bottom + 14}
            textAnchor="middle"
            fontSize="9"
            fill="var(--text-muted)"
          >
            {d.time}
          </text>
        ) : null
      )}
    </svg>
  );
}

function ProtocolBar() {
  const total = MOCK_PROTOCOL_DIST.reduce((s, d) => s + d.pct, 0);
  const colors = [
    'var(--accent-primary)',
    'var(--severity-high)',
    'var(--severity-medium)',
    'var(--severity-low)',
    'var(--text-muted)',
  ];

  return (
    <div className="proto-bar-wrap">
      <div className="proto-bar">
        {MOCK_PROTOCOL_DIST.map((d, i) => (
          <div
            key={d.protocol}
            className="proto-bar-seg"
            style={{ width: `${(d.pct / total) * 100}%`, background: colors[i] }}
            title={`${d.protocol} ${d.pct}%`}
          />
        ))}
      </div>
      <div className="proto-legend">
        {MOCK_PROTOCOL_DIST.map((d, i) => (
          <span key={d.protocol} className="proto-legend-item">
            <span className="proto-legend-dot" style={{ background: colors[i] }} />
            {d.protocol} {d.pct}%
          </span>
        ))}
      </div>
    </div>
  );
}

export function Traffic() {
  return (
    <div className="traffic-page">
      <div className="demo-banner" role="status" style={{ marginBottom: 'var(--space-4)' }}>
        All traffic data shown is DEMO/MOCK — not real production telemetry.
      </div>

      <div className="traffic-grid">
        <div className="traffic-col-throughput">
          <div className="panel" style={{ height: '100%' }}>
            <div className="panel-header">
              <span className="panel-title">Observed Throughput (24 h)</span>
            </div>
            <div className="panel-body">
              <TrafficChart />
            </div>
          </div>
        </div>

        <div className="traffic-col-protocol">
          <div className="panel" style={{ height: '100%' }}>
            <div className="panel-header">
              <span className="panel-title">Protocol Distribution</span>
            </div>
            <div className="panel-body">
              <ProtocolBar />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
