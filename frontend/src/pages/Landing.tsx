import { Link } from 'react-router-dom';
import { useState } from 'react';
import { UnidirectionalThreatStream } from '../components/UnidirectionalThreatStream';
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

/* ── Deep-dive content moved from Threats & AI Detection dashboard pages ── */

const THREAT_DEEP_DIVE = [
  {
    label: 'Volumetric DDoS',
    description: 'Detection of distributed denial-of-service attacks through traffic volume and protocol anomaly analysis.',
    indicators: ['SYN flood patterns', 'Abnormal packet rates', 'Source entropy elevation', 'Protocol ratio anomalies'],
  },
  {
    label: 'C2 Beaconing',
    description: 'Identification of command-and-control communication patterns from compromised hosts.',
    indicators: ['Periodic connection patterns', 'Low-volume persistent flows', 'Unusual destination diversity', 'Timing regularity'],
  },
  {
    label: 'DGA / DNS Tunnel',
    description: 'Detection of algorithmically generated domains and covert DNS tunneling channels.',
    indicators: ['High-entropy domain names', 'Abnormal DNS query volume', 'Large TXT record responses', 'NXDOMAIN ratios'],
  },
  {
    label: 'Encrypted Malware',
    description: 'Identification of malicious payloads hidden within encrypted TLS sessions using metadata analysis.',
    indicators: ['JA3/JA4 fingerprint anomalies', 'Certificate irregularities', 'Unusual TLS version usage', 'Flow size patterns'],
  },
  {
    label: 'Recon / Port Scan',
    description: 'Detection of network reconnaissance activities and systematic port scanning.',
    indicators: ['Sequential port access', 'High destination port diversity', 'Failed connection ratios', 'Sweep patterns'],
  },
  {
    label: 'Data Exfiltration',
    description: 'Identification of unauthorized data transfers and anomalous outbound traffic patterns.',
    indicators: ['Unusual outbound volume', 'Off-hours data transfers', 'Asymmetric flow ratios', 'Rare destination IPs'],
  },
  {
    label: 'Unknown Threat',
    description: 'Detection of previously unseen or highly unusual behavior via statistical baseline deviation.',
    indicators: ['High Z-score deviations', 'Unusual geographic destinations', 'Sudden protocol usage shifts', 'Volume spikes outside historical bounds'],
  },
];

const DETECTOR_DEEP_DIVE = [
  {
    label: 'DDoS Detector',
    description: 'Detects volumetric Denial-of-Service patterns by observing passive traffic flow statistics. Classifies high-volume packet anomalies and SYN flood patterns.',
    threats: ['Volumetric DDoS'],
    method: 'Flow-feature analysis + River online learning',
  },
  {
    label: 'Recon Detector',
    description: 'Identifies reconnaissance and port-scanning behaviour from passive connection telemetry. Tracks sweep patterns across observed source/destination pairs.',
    threats: ['Recon / Port Scan'],
    method: 'Sliding-window sweep detection + XGBoost classifier',
  },
  {
    label: 'DNS / DGA / Tunneling Detector',
    description: 'Analyses passive DNS query patterns to detect domain generation algorithm (DGA) activity and DNS-based data tunneling. Operates solely on observed DNS telemetry.',
    threats: ['DGA / DNS Tunnel'],
    method: 'N-gram language model + entropy analysis',
  },
  {
    label: 'TLS / C2 Detector',
    description: 'Classifies encrypted session metadata to identify botnet Command-and-Control beaconing and malware communication within TLS flows without decrypting payloads.',
    threats: ['C2 Beaconing', 'Encrypted Malware'],
    method: 'TLS metadata features + scikit-learn ensemble',
  },
  {
    label: 'Exfiltration Detector',
    description: 'Detects anomalous outbound data volumes that are consistent with data exfiltration. Relies on passive flow-level byte and packet counters.',
    threats: ['Data Exfiltration'],
    method: 'Statistical baseline deviation + River adaptive model',
  },
];

export function Landing() {
  const [deepDiveOpen, setDeepDiveOpen] = useState(false);

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

          {/* Right: Visual */}
          <div className="hero-visual-frame uts-hero-frame">
            <UnidirectionalThreatStream />
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
              How network packets travel from passive sensors to the security analyst's browser.
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

      {/* ── More about Irochi — Deep Dive Section ── */}
      <section className="landing-deep-dive scroll-reveal">
        <div className="landing-section-container">
          <div className="deep-dive-toggle-area">
            <button
              className={`deep-dive-trigger ${deepDiveOpen ? 'open' : ''}`}
              onClick={() => setDeepDiveOpen(!deepDiveOpen)}
              aria-expanded={deepDiveOpen}
            >
              <div className="deep-dive-trigger-content">
                <div className="deep-dive-trigger-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <path d="M12 16v-4" />
                    <path d="M12 8h.01" />
                  </svg>
                </div>
                <div className="deep-dive-trigger-text">
                  <span className="deep-dive-trigger-label">More about Irochi</span>
                  <span className="deep-dive-trigger-sub">Detailed threat intelligence models & AI detection architecture</span>
                </div>
              </div>
              <svg className="deep-dive-chevron" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>
          </div>

          <div className={`deep-dive-content ${deepDiveOpen ? 'expanded' : ''}`}>
            {/* Threat Intelligence Deep Dive */}
            <div className="deep-dive-block">
              <div className="deep-dive-block-header">
                <div className="section-eyebrow">THREAT INTELLIGENCE</div>
                <h3 className="deep-dive-block-title">Seven Threat Classification Models</h3>
                <p className="deep-dive-block-desc">
                  Each threat type is detected using specialized classifiers trained on specific indicators. Below is a detailed breakdown of every threat category and its key detection signals.
                </p>
              </div>

              <div className="deep-dive-threat-grid">
                {THREAT_DEEP_DIVE.map((threat) => (
                  <div key={threat.label} className="deep-dive-threat-card">
                    <h4 className="deep-dive-card-title">{threat.label}</h4>
                    <p className="deep-dive-card-desc">{threat.description}</p>
                    <div className="deep-dive-indicators">
                      <span className="deep-dive-indicators-label">Key Indicators</span>
                      <ul className="deep-dive-indicator-list">
                        {threat.indicators.map((ind) => (
                          <li key={ind}>{ind}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Detection Deep Dive */}
            <div className="deep-dive-block">
              <div className="deep-dive-block-header">
                <div className="section-eyebrow">AI DETECTION MODULES</div>
                <h3 className="deep-dive-block-title">Five Detector Modules</h3>
                <p className="deep-dive-block-desc">
                  Each module is a logical component of the AI pipeline, not a separate microservice. A single detector may classify multiple threat types. Below are the modules and the machine-learning methods they employ.
                </p>
              </div>

              <div className="deep-dive-detector-grid">
                {DETECTOR_DEEP_DIVE.map((det) => (
                  <div key={det.label} className="deep-dive-detector-card">
                    <h4 className="deep-dive-card-title">{det.label}</h4>
                    <p className="deep-dive-card-desc">{det.description}</p>
                    <div className="deep-dive-detector-meta">
                      <div className="deep-dive-detector-field">
                        <span className="deep-dive-field-label">Classified threats</span>
                        <div className="deep-dive-tags">
                          {det.threats.map((t) => (
                            <span key={t} className="deep-dive-tag">{t}</span>
                          ))}
                        </div>
                      </div>
                      <div className="deep-dive-detector-field">
                        <span className="deep-dive-field-label">Detection method</span>
                        <span className="mono deep-dive-method">{det.method}</span>
                      </div>
                    </div>
                  </div>
                ))}
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
