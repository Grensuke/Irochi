/**
 * Detector Health panel.
 * Technical system health overview for the 5 logical detection modules.
 */

const MOCK_DETECTORS = [
  { id: 'ddos', name: 'DDoS Detector', status: 'active', info: 'Operational' },
  { id: 'recon', name: 'Recon Detector', status: 'active', info: 'Operational' },
  { id: 'dns', name: 'DNS / DGA Tunneling', status: 'degraded', info: 'Model artifact unavailable in current deployment' },
];

export function DetectorHealth() {
  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Detection Engine Status</span>
      </div>
      <div className="detector-health-grid">
        {MOCK_DETECTORS.map(det => (
          <div key={det.id} className="detector-health-row" title={det.info}>
            <span className={`detector-status-dot ${det.status}`} />
            <span className="detector-name">{det.name}</span>
            <span className="mono" style={{ fontSize: '0.68rem', color: det.status === 'degraded' ? 'var(--severity-medium)' : 'var(--text-muted)', textAlign: 'right', flex: 1 }}>{det.status.toUpperCase()}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
