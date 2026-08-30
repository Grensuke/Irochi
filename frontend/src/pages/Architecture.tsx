import './Architecture.css';

const FLOW_STEPS = [
  {
    phase: 'Telemetry Ingestion',
    items: [
      { name: 'PCAP / Network Taps', desc: 'Raw packets are passively mirrored via network SPAN ports or physical hardware data diodes.' },
      { name: 'Zeek Sensor Engine', desc: 'Zeek decodes mirrored traffic into rich protocol logs (HTTP, DNS, SSL, etc.) without interacting with entities.' },
      { name: 'NetFlow / IPFIX Router', desc: 'Unidirectional routers export layer-3 flow data, which bypasses Zeek to load balancer directly.' }
    ]
  },
  {
    phase: 'Normalization & Queueing',
    items: [
      { name: 'Python Ingest Normalizer', desc: 'Converts multi-source network signals into a unified data contract matching the Canonical Event Schema.' },
      { name: 'Redpanda Streaming Cluster', desc: 'Buffer telemetry logs into decoupled streaming queues (e.g. topic connections, topic dns) to prevent packet loss under stress.' }
    ]
  },
  {
    phase: 'Feature Processing & Detection',
    items: [
      { name: 'Feature Window Extractors', desc: 'Applies sliding windows to stream vectors, building behavioral metrics (like connection rates, domain entropy).' },
      { name: 'Logical Detector Modules', desc: 'Runs tabular ML models (XGBoost) and sequential stream classifiers (River) to flag threat vectors.' }
    ]
  },
  {
    phase: 'Alert Persistence & Fan-Out',
    items: [
      { name: 'Alert Engine', desc: 'Validates classifications, checks thresholds, assigns confidence, and formats detailed evidence packets.' },
      { name: 'PostgreSQL DB (Commit Boundary)', desc: 'The durable source of truth. Every alert must successfully insert and await database COMMIT.' },
      { name: 'Redis Pub/Sub Layer', desc: 'Once persistent commit is completed, the alert is published to the Redis channel to trigger browser notifications.' }
    ]
  },
  {
    phase: 'FastAPI Boundary (Gateway)',
    items: [
      { name: 'FastAPI REST & WS Services', desc: 'Serves secure dashboards via HTTP REST endpoints and feeds live alerts to clients over WebSockets.' }
    ]
  },
  {
    phase: 'React Dashboard (Analyst GUI)',
    items: [
      { name: 'React + Router v7 Web Application', desc: 'A dense console rendering live WebSocket feeds, detailed evidence lists, and triage workspaces for SOC analysts.' }
    ]
  }
];

export function Architecture() {
  return (
    <div className="architecture-page">
      <div className="architecture-container">
        {/* Header */}
        <section className="arch-header scroll-reveal">
          <div className="section-eyebrow">SYSTEM ARCHITECTURE</div>
          <h1 className="arch-title">Unidirectional Data Pipeline</h1>
          <p className="arch-subtitle">
            Irochi uses a decoupled, high-performance architecture to ingest, normalize, analyze, and present network threat intelligence without altering telemetry pathways.
          </p>
        </section>

        {/* Browser Boundary Invariant Card */}
        <section className="boundary-card scroll-reveal">
          <div className="boundary-card-glow" />
          <h2 className="boundary-title">The Secure Gateway Invariant</h2>
          <p className="boundary-text">
            For operational security and architectural integrity, the browser never communicates directly with Redpanda streams, Redis Pub/Sub, or the PostgreSQL database. All query transactions, session authentication, and WebSocket live feeds are brokered exclusively by the <strong>FastAPI Backend Gateway</strong>.
          </p>
        </section>

        {/* Decoupled Stages Walkthrough */}
        <section className="pipeline-walkthrough scroll-reveal">
          <h2 className="section-title-sm">Step-by-Step Data Flow</h2>
          <p className="section-body-text" style={{ marginBottom: 'var(--space-6)' }}>
            Telemetry travels strictly one-way from the network mirrors to the analyst dashboard.
          </p>

          <div className="flow-timeline">
            {FLOW_STEPS.map((stage, idx) => (
              <div key={stage.phase} className="flow-stage">
                <div className="flow-stage-header">
                  <span className="flow-stage-num mono">{idx + 1}</span>
                  <h3 className="flow-stage-title">{stage.phase}</h3>
                </div>

                <div className="flow-items-grid">
                  {stage.items.map((item) => (
                    <div key={item.name} className="flow-item-card">
                      <h4 className="flow-item-name">{item.name}</h4>
                      <p className="flow-item-desc">{item.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
