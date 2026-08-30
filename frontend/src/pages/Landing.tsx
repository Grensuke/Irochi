import { Link } from 'react-router-dom';
import './Landing.css';

const CAPABILITIES = [
  { 
    title: 'Volumetric & Protocol DDoS', 
    desc: 'Detect distributed denial-of-service attempts by monitoring traffic rate anomalies and protocol-compliance drift.', 
    signal: 'Packet frequency, packet sizes, protocol headers, flow count' 
  },
  { 
    title: 'Botnet C2 Beaconing', 
    desc: 'Identify covert outbound beacon signals and persistent communication patterns with remote control addresses.', 
    signal: 'Jitter thresholds, request interval entropy, TCP states, session duration' 
  },
  { 
    title: 'DGA & DNS Tunneling', 
    desc: 'Identify algorithmically generated domain lookups and nested query exfiltration attempts over standard DNS queries.', 
    signal: 'Query entropy, character distributions, record count, response sizes' 
  },
  { 
    title: 'Encrypted Malware TLS/C2', 
    desc: 'Detect persistent malicious sessions and malware telemetry within encrypted connections using metadata signals.', 
    signal: 'TLS client hellos, certificate details, server name indicators (SNI)' 
  },
  { 
    title: 'Reconnaissance & Port Scanning', 
    desc: 'Expose remote profiling attempts, systematic sweep scans, and port scans mapping network architecture.', 
    signal: 'Sequential connection failures, port frequency, source IP behavior' 
  },
  { 
    title: 'Data Exfiltration', 
    desc: 'Pinpoint large, continuous, or anomalous outbound payload transfers crossing secure segments.', 
    signal: 'Outbound flow volume, byte-to-packet ratios, host baselines' 
  },
];

const PIPELINE_STAGES = [
  { step: '01', name: 'Telemetry Mirroring', desc: 'Passively mirror unidirectional packets into sensors without interrupting live networks.' },
  { step: '02', name: 'Zeek & Flow Extraction', desc: 'Generate normalized network logging and connection metadata in near-real-time.' },
  { step: '03', name: 'Ingest Normalization', desc: 'Parse network telemetry into structured event schema, filtering internal noise.' },
  { step: '04', name: 'Streaming Transport', desc: 'Stream events through high-throughput Redpanda topics for decoupled ingestion.' },
  { step: '05', name: 'AI & Rule Detections', desc: 'Evaluate features using XGBoost and River online-learning threat models.' },
  { step: '06', name: 'Security Dashboards', desc: 'Deliver evidence-backed alerts and contextual intelligence to SOC analysts.' }
];

export function Landing() {
  return (
    <div className="landing-page-wrap">
      {/* Hero Section */}
      <section className="landing-hero">
        <div className="landing-spotlight-beam" />
        <div className="landing-hero-container">
          <div className="hero-text-content">
            <div className="hero-eyebrow">PASSIVE NETWORK SECURITY INTELLIGENCE</div>
            <h1 className="hero-title">
              See threats in motion.<br />
              Act with evidence.
            </h1>
            <p className="hero-description">
              Irochi detects suspicious patterns in unidirectional IP traffic using passive telemetry, streaming analysis, and evidence-backed alerts. Designed for environments where traffic interruption is not an option.
            </p>
            <div className="hero-actions">
              <Link to="/login" className="btn btn-primary btn-lg">
                Explore the platform
              </Link>
              <Link to="/architecture" className="btn btn-ghost btn-lg">
                View architecture
              </Link>
            </div>

            {/* Passive Warning Banner */}
            <div className="passive-warning-banner">
              <span className="warning-indicator" />
              <span className="warning-text">
                <strong>Observational System:</strong> Irochi is purely passive/read-only. It does not block traffic, re-contact sources, or decrypt payloads.
              </span>
            </div>
          </div>

          {/* Refined Globe Graphic Preview */}
          <div className="hero-visual-frame">
            <svg className="hero-globe-svg" width="460" height="460" viewBox="0 0 400 400" aria-hidden="true">
              <defs>
                <radialGradient id="globeGlow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="var(--accent-primary)" stopOpacity="0.3" />
                  <stop offset="100%" stopColor="transparent" stopOpacity="0" />
                </radialGradient>
                <filter id="scannerGlow" x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur stdDeviation="6" result="blur" />
                  <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
              </defs>
              {/* Background Glow */}
              <circle cx="200" cy="200" r="180" fill="url(#globeGlow)" />
              {/* Outer boundary */}
              <circle cx="200" cy="200" r="170" stroke="var(--border-strong)" strokeWidth="1" fill="none" />
              
              {/* Longitude bands */}
              <ellipse cx="200" cy="200" rx="140" ry="170" stroke="var(--border-subtle)" strokeWidth="0.8" fill="none" className="globe-ellipse" />
              <ellipse cx="200" cy="200" rx="90" ry="170" stroke="var(--border-subtle)" strokeWidth="0.8" fill="none" className="globe-ellipse" />
              <ellipse cx="200" cy="200" rx="40" ry="170" stroke="var(--border-subtle)" strokeWidth="0.8" fill="none" className="globe-ellipse" />
              
              {/* Latitude bands */}
              <ellipse cx="200" cy="200" rx="170" ry="130" stroke="var(--border-subtle)" strokeWidth="0.8" fill="none" className="globe-ellipse" />
              <ellipse cx="200" cy="200" rx="170" ry="80" stroke="var(--border-subtle)" strokeWidth="0.8" fill="none" className="globe-ellipse" />
              <ellipse cx="200" cy="200" rx="170" ry="30" stroke="var(--border-subtle)" strokeWidth="0.8" fill="none" className="globe-ellipse" />
              
              {/* Dashboard targets and arcs (glowing connection links) */}
              <path className="globe-arc arc-1" d="M 60 200 Q 200 80 340 200" stroke="var(--accent-primary)" strokeWidth="1.2" strokeDasharray="8 80" fill="none" />
              <path className="globe-arc arc-2" d="M 90 120 Q 200 280 310 280" stroke="var(--accent-cyan)" strokeWidth="1.2" strokeDasharray="8 80" fill="none" />
              <path className="globe-arc arc-3" d="M 110 110 Q 200 160 290 290" stroke="var(--accent-cyan)" strokeWidth="1" strokeDasharray="6 60" fill="none" opacity="0.6" />
              <path className="globe-arc arc-4" d="M 60 200 Q 200 320 340 200" stroke="var(--severity-critical)" strokeWidth="1" strokeDasharray="10 100" fill="none" opacity="0.4" />
              <path className="globe-arc arc-5" d="M 200 70 Q 150 200 200 330" stroke="var(--accent-primary)" strokeWidth="1.2" strokeDasharray="8 80" fill="none" />

              {/* Pulse intersections (Highly Highlighted, Concentric, Glowing Nodes) */}
              {/* Central Core Node */}
              <g transform="translate(200, 200)">
                <circle r="5" fill="var(--accent-primary)" />
                <circle r="12" fill="var(--accent-primary)" fillOpacity="0.2" className="node-pulse" />
                <circle r="22" fill="var(--accent-primary)" fillOpacity="0.08" className="node-pulse-slow" />
                <text x="12" y="-12" textAnchor="start" fontSize="9" fill="var(--text-secondary)" fontFamily="var(--font-mono)" fontWeight="600" opacity="0.85">SENSING_CORE</text>
              </g>

              {/* Critical Threat Node */}
              <g transform="translate(60, 200)">
                <circle r="6" fill="var(--severity-critical)" />
                <circle r="14" fill="var(--severity-critical)" fillOpacity="0.25" className="node-pulse" />
                <circle r="26" fill="var(--severity-critical)" fillOpacity="0.1" className="node-pulse-slow" />
                <text x="-12" y="4" textAnchor="end" fontSize="9" fill="var(--severity-critical)" fontFamily="var(--font-mono)" fontWeight="700">CRITICAL_ALERT</text>
              </g>

              {/* High Threat Node */}
              <g transform="translate(340, 200)">
                <circle r="5.5" fill="var(--severity-high)" />
                <circle r="13" fill="var(--severity-high)" fillOpacity="0.2" className="node-pulse" />
                <circle r="24" fill="var(--severity-high)" fillOpacity="0.08" className="node-pulse-slow" />
                <text x="12" y="4" textAnchor="start" fontSize="9" fill="var(--severity-high)" fontFamily="var(--font-mono)" fontWeight="700">HIGH_RISK</text>
              </g>

              {/* Beaconing C2 Node */}
              <g transform="translate(110, 110)">
                <circle r="4" fill="var(--accent-cyan)" />
                <circle r="10" fill="var(--accent-cyan)" fillOpacity="0.2" className="node-pulse-slow" />
                <text x="0" y="-12" textAnchor="middle" fontSize="8" fill="var(--accent-cyan)" fontFamily="var(--font-mono)" fontWeight="600" opacity="0.8">C2_BEACON</text>
              </g>

              {/* Active Agent Node */}
              <g transform="translate(290, 290)">
                <circle r="4" fill="var(--accent-cyan)" />
                <circle r="10" fill="var(--accent-cyan)" fillOpacity="0.2" className="node-pulse" />
                <text x="0" y="20" textAnchor="middle" fontSize="8" fill="var(--accent-cyan)" fontFamily="var(--font-mono)" fontWeight="600" opacity="0.8">SENSING_NODE</text>
              </g>

              {/* Top Node */}
              <g transform="translate(200, 70)">
                <circle r="3" fill="var(--accent-primary)" />
                <circle r="8" fill="var(--accent-primary)" fillOpacity="0.15" className="node-pulse" />
              </g>

              {/* Bottom Node */}
              <g transform="translate(200, 330)">
                <circle r="3" fill="var(--severity-low)" />
                <circle r="8" fill="var(--severity-low)" fillOpacity="0.15" className="node-pulse-slow" />
              </g>

              <g transform="translate(110, 290)">
                <circle r="3.5" fill="var(--severity-medium)" />
                <circle r="9" fill="var(--severity-medium)" fillOpacity="0.18" className="node-pulse" />
              </g>
              <g transform="translate(290, 110)">
                <circle r="3.5" fill="var(--severity-info)" />
                <circle r="9" fill="var(--severity-info)" fillOpacity="0.18" className="node-pulse-slow" />
              </g>
            </svg>
            <div className="hero-globe-overlay">
              <span className="telemetry-log mono">10.0.3.42:53 &gt; DNS Tunnelling Alert</span>
              <span className="telemetry-log mono">192.168.24.17 &gt; DDoS Volumetric SYN</span>
            </div>
          </div>
        </div>
      </section>

      {/* Trust Strip */}
      <section className="landing-trust-strip scroll-reveal">
        <div className="trust-strip-container">
          <div className="trust-item">
            <span className="trust-label">Passive by design</span>
            <span className="trust-sub">Zero network performance footprint</span>
          </div>
          <div className="trust-item">
            <span className="trust-label">Metadata-first analysis</span>
            <span className="trust-sub">Flow and Zeek protocol metadata only</span>
          </div>
          <div className="trust-item">
            <span className="trust-label">Near-real-time alerting</span>
            <span className="trust-sub">WebSocket streaming delivery</span>
          </div>
          <div className="trust-item">
            <span className="trust-label">Analyst-controlled workflow</span>
            <span className="trust-sub">Triage with contextual evidence</span>
          </div>
        </div>
      </section>

      {/* Problem vs Approach Section */}
      <section className="landing-problem-approach scroll-reveal">
        <div className="landing-section-container">
          <div className="grid-2-col">
            <div className="problem-panel">
              <div className="section-eyebrow">THE OPERATIONAL CHALLENGE</div>
              <h2 className="section-title-sm">Monitoring networks you cannot interrupt</h2>
              <p className="section-body-text">
                Critical infrastructure networks, manufacturing control segments, and industrial environments carry high-risk IP traffic where active scanning, inline firewalls, or packet mitigation cannot be deployed. Conventional security solutions often introduce latency, configuration hazards, or active probes that risk operational stability.
              </p>
            </div>
            <div className="approach-panel">
              <div className="section-eyebrow">THE IROCHI APPROACH</div>
              <h2 className="section-title-sm">Intelligence without active interference</h2>
              <p className="section-body-text">
                Irochi operates as a passive observer. By reading mirrored network traffic or NetFlow telemetry, the system feeds flow structures and protocol metadata through machine-learning detection engines. Analysts receive detailed confidence scoring and supporting evidence to triage alerts manually—guaranteeing operational safety.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Capability Section */}
      <section className="landing-capabilities scroll-reveal">
        <div className="landing-section-container">
          <div style={{ textAlign: 'center', marginBottom: 'var(--space-10)' }}>
            <div className="section-eyebrow">THREAT DETECTABILITY</div>
            <h2 className="section-title">Six Threat Capabilities</h2>
            <p className="section-subtitle">
              Passively classifying network risks into core capabilities through specialized detection models.
            </p>
          </div>

          <div className="capabilities-grid">
            {CAPABILITIES.map((cap) => (
              <div key={cap.title} className="cap-card">
                <div className="cap-card-border-glow" />
                <div className="cap-card-header">
                  <div className="cap-technical-marker">SIGNAL SELECTOR</div>
                  <h3 className="cap-title">{cap.title}</h3>
                </div>
                <p className="cap-desc">{cap.desc}</p>
                <div className="cap-meta">
                  <span className="cap-meta-label">INPUT DATA:</span>
                  <span className="cap-meta-value mono">{cap.signal}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Simplified Detection Pipeline */}
      <section className="landing-pipeline scroll-reveal">
        <div className="landing-section-container">
          <div style={{ textAlign: 'center', marginBottom: 'var(--space-10)' }}>
            <div className="section-eyebrow">DATA ARCHITECTURE</div>
            <h2 className="section-title">Telemetry & Alert Pipeline</h2>
            <p className="section-subtitle">
              How network packets travel from passive sensors to the security analyst’s browser.
            </p>
          </div>

          <div className="pipeline-container">
            {PIPELINE_STAGES.map((stage) => (
              <div key={stage.step} className="pipeline-step">
                <div className="pipeline-badge mono">{stage.step}</div>
                <h3 className="pipeline-name">{stage.name}</h3>
                <p className="pipeline-desc">{stage.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Evidence Alert Preview Section */}
      <section className="landing-preview scroll-reveal">
        <div className="landing-section-container">
          <div className="grid-2-col" style={{ alignItems: 'center', gap: 'var(--space-12)' }}>
            <div>
              <div className="section-eyebrow">CONTEXT-RICH EVIDENCE</div>
              <h2 className="section-title-sm">No alert without explanation</h2>
              <p className="section-body-text" style={{ marginBottom: 'var(--space-5)' }}>
                Irochi avoids single-score black-box alerting. Every alert contains the precise source and destination metadata, the specific detector responsible, an observation window, and a detailed summary of the supporting parameters observed in the traffic.
              </p>
              <Link to="/documentation" className="btn btn-ghost">
                Read about the alert model
              </Link>
            </div>

            {/* Mock Alert Preview Card */}
            <div className="preview-alert-card">
              <div className="preview-alert-header">
                <div className="preview-alert-title-row">
                  <span className="mono preview-alert-id">ALT-004182</span>
                  <span className="severity-badge critical">Critical</span>
                </div>
                <h3 className="preview-threat-label">Volumetric DDoS Attack</h3>
              </div>
              <div className="preview-alert-body">
                <div className="preview-grid-mini">
                  <div>
                    <span className="mini-label">SOURCE</span>
                    <span className="mini-value mono">192.168.24.17</span>
                  </div>
                  <div>
                    <span className="mini-label">DESTINATION</span>
                    <span className="mini-value mono">10.42.8.21:443</span>
                  </div>
                  <div>
                    <span className="mini-label">CONFIDENCE</span>
                    <span className="mini-value mono" style={{ color: 'var(--severity-critical)' }}>96.0%</span>
                  </div>
                  <div>
                    <span className="mini-label">WORKFLOW STATUS</span>
                    <span className="mini-value mono" style={{ color: 'var(--status-new)' }}>New</span>
                  </div>
                </div>
                <div className="preview-evidence">
                  <span className="mini-label">EVIDENCE OBSERVED</span>
                  <p className="evidence-text">
                    Traffic characteristics strongly match the learned TCP SYN flood profile. High frequency connection requests inside a 10s observation window.
                  </p>
                </div>
                <div className="preview-phase">
                  <span className="phase-badge live">Live Mode</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="landing-cta scroll-reveal">
        <div className="landing-section-container" style={{ textAlign: 'center' }}>
          <h2 className="cta-headline">Inspect unidirectional telemetry with confidence</h2>
          <p className="cta-sub">
            Open the live operational console or inspect the architecture diagrams.
          </p>
          <div className="cta-actions">
            <Link to="/login" className="btn btn-primary btn-lg">
              Explore the platform
            </Link>
            <Link to="/architecture" className="btn btn-ghost btn-lg">
              View architecture
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
