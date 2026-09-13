/**
 * Traffic Monitor page.
 *
 * All live telemetry has been audited. Since the backend does not currently 
 * expose real raw throughput or protocol distribution, this page displays a 
 * truthful idle/unavailable state instead of simulated fake metrics.
 */



function TrafficChartEmptyState() {
  return (
    <div style={{ height: '120px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--bg-card)', border: '1px dashed var(--border-subtle)', borderRadius: 'var(--radius-md)' }}>
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginBottom: '8px' }}>
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
      </svg>
      <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>Awaiting telemetry. Live traffic metrics will populate after network ingestion.</span>
    </div>
  );
}

function ProtocolBarEmptyState() {
  return (
     <div style={{ height: '60px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--bg-card)', border: '1px dashed var(--border-subtle)', borderRadius: 'var(--radius-md)' }}>
      <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>Protocol distribution unavailable</span>
    </div>
  );
}

export function Traffic() {
  return (
    <div className="traffic-page">
      <div className="traffic-grid">
        <div className="traffic-col-throughput">
          <div className="panel" style={{ height: '100%' }}>
            <div className="panel-header">
              <span className="panel-title">Observed Throughput (24 h)</span>
            </div>
            <div className="panel-body">
              <TrafficChartEmptyState />
            </div>
          </div>
        </div>

        <div className="traffic-col-protocol">
          <div className="panel" style={{ height: '100%' }}>
            <div className="panel-header">
              <span className="panel-title">Protocol Distribution</span>
            </div>
            <div className="panel-body">
              <ProtocolBarEmptyState />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
