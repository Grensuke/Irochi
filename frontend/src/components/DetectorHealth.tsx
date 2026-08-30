/**
 * Detector Health panel.
 * Technical system health overview for the 5 logical detection modules.
 */

const MOCK_DETECTORS = [
  { id: 'ddos', name: 'DDoS Detector', status: 'active', rate: '2.1K fps', lastEvent: '12s ago' },
  { id: 'recon', name: 'Recon Detector', status: 'active', rate: '412 fps', lastEvent: '2m ago' },
  { id: 'dns', name: 'DNS / DGA Detector', status: 'processing', rate: '850 qps', lastEvent: '4s ago' },
  { id: 'c2', name: 'C2 Beacon Detector', status: 'active', rate: '120 fps', lastEvent: '45s ago' },
  { id: 'exfil', name: 'Exfiltration Detector', status: 'active', rate: '18 fps', lastEvent: '8m ago' },
];

export function DetectorHealth() {
  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Detection Engine Status <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginLeft: '8px', verticalAlign: 'middle' }}>(SIMULATED DEMO)</span></span>
      </div>
      <div className="detector-health-grid">
        {MOCK_DETECTORS.map(det => (
          <div key={det.id} className="detector-health-row">
            <span className={`detector-status-dot ${det.status}`} />
            <span className="detector-name">{det.name}</span>
            <span className="mono" style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{det.rate}</span>
            <span className="mono" style={{ fontSize: '0.68rem', color: 'var(--text-muted)', width: '45px', textAlign: 'right' }}>{det.lastEvent}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
