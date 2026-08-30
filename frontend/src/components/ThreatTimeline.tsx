/**
 * Threat Timeline
 * A clean time-series chart showing alert volume/activity over time.
 * Uses native SVG, no external libraries.
 */

const MOCK_TIMELINE_DATA = [
  12, 15, 8, 14, 22, 18, 30, 45, 38, 25, 20, 15, 18, 22, 28, 35, 42, 38, 30, 24, 18, 15, 10, 8
];

const W = 600;
const H = 140;
const PAD = { top: 10, right: 10, bottom: 20, left: 30 };

export function ThreatTimeline() {
  const maxVal = Math.max(...MOCK_TIMELINE_DATA, 1);
  
  const scaleX = (i: number) => PAD.left + (i / (MOCK_TIMELINE_DATA.length - 1)) * (W - PAD.left - PAD.right);
  const scaleY = (v: number) => PAD.top + (1 - v / maxVal) * (H - PAD.top - PAD.bottom);

  const points = MOCK_TIMELINE_DATA.map((d, i) => `${scaleX(i)},${scaleY(d)}`).join(' ');
  const areaPoints = [
    `${scaleX(0)},${H - PAD.bottom}`,
    ...MOCK_TIMELINE_DATA.map((d, i) => `${scaleX(i)},${scaleY(d)}`),
    `${scaleX(MOCK_TIMELINE_DATA.length - 1)},${H - PAD.bottom}`,
  ].join(' ');

  return (
    <div className="panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header">
        <span className="panel-title">Threat Activity (24h)</span>
      </div>
      <div className="panel-body" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="100%" preserveAspectRatio="none" style={{ display: 'block' }}>
          {/* Grid lines */}
          {[0, 0.5, 1].map(t => (
            <line
              key={t}
              x1={PAD.left} y1={scaleY(maxVal * t)}
              x2={W - PAD.right} y2={scaleY(maxVal * t)}
              stroke="var(--border-subtle)"
              strokeDasharray="2,2"
            />
          ))}
          
          {/* Y Axis labels */}
          {[0, 0.5, 1].map(t => (
            <text
              key={t}
              x={PAD.left - 6} y={scaleY(maxVal * t) + 3}
              textAnchor="end" fontSize="9" fill="var(--text-muted)" fontFamily="var(--font-mono)"
            >
              {Math.round(maxVal * t)}
            </text>
          ))}

          {/* Area */}
          <polygon className="threat-timeline-area" points={areaPoints} fill="var(--accent-primary)" fillOpacity="0.05" />
          
          {/* Base Static Line */}
          <polyline className="threat-timeline-line" points={points} fill="none" stroke="var(--accent-primary)" strokeWidth="1.5" strokeLinejoin="round" opacity="0.6" />
          
          {/* Flow Motion Overlay Line */}
          <polyline className="chart-flow-line" points={points} fill="none" stroke="var(--accent-cyan)" strokeWidth="1.8" strokeLinejoin="round" />
        </svg>
      </div>
    </div>
  );
}
