import { Link } from 'react-router-dom';
import './Landing.css';

const CAPABILITIES = [
  { title: 'Volumetric / Protocol DDoS', desc: 'Detect distributed denial-of-service attacks through traffic volume and protocol anomalies.', icon: '⚡' },
  { title: 'Botnet C2 Beaconing', desc: 'Identify command-and-control communication patterns from compromised hosts.', icon: '📡' },
  { title: 'DGA / DNS Tunneling', desc: 'Detect algorithmically generated domains and covert DNS tunneling channels.', icon: '🔗' },
  { title: 'Encrypted Malware', desc: 'Identify malicious payloads hidden within encrypted TLS sessions using metadata analysis.', icon: '🔒' },
  { title: 'Reconnaissance / Port Scanning', desc: 'Detect network reconnaissance activities and systematic port scanning.', icon: '🔍' },
  { title: 'Data Exfiltration', desc: 'Identify unauthorized data transfers and anomalous outbound traffic patterns.', icon: '📤' },
];

export function Landing() {
  return (
    <div className="landing">
      {/* Header */}
      <header className="landing-header">
        <div className="landing-brand">
          <svg width="22" height="22" viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="10" r="8" stroke="var(--accent-primary)" strokeWidth="1.5" fill="none" />
            <circle cx="10" cy="10" r="3" fill="var(--accent-primary)" />
            <line x1="10" y1="2" x2="10" y2="6" stroke="var(--accent-primary)" strokeWidth="1.5" />
            <line x1="10" y1="14" x2="10" y2="18" stroke="var(--accent-primary)" strokeWidth="1.5" />
            <line x1="2" y1="10" x2="6" y2="10" stroke="var(--accent-primary)" strokeWidth="1.5" />
            <line x1="14" y1="10" x2="18" y2="10" stroke="var(--accent-primary)" strokeWidth="1.5" />
          </svg>
          <span>IROCHI</span>
        </div>
        <Link to="/login" className="btn btn-primary btn-sm">Sign In</Link>
      </header>

      {/* Hero */}
      <section className="landing-hero">
        <div className="hero-content">
          <div className="hero-badge">SIH 2026 — Problem Statement SIH26145</div>
          <h1>Passive Network<br />Threat Intelligence</h1>
          <p className="hero-subtitle">
            Real-time detection and security intelligence for enterprise networks.
            Irochi passively monitors network telemetry to identify threats —
            without disrupting traffic or requiring inline deployment.
          </p>
          <div className="hero-actions">
            <Link to="/login" className="btn btn-primary btn-lg">
              Get Started
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 8h10M9 4l4 4-4 4"/></svg>
            </Link>
          </div>
          <div className="hero-note">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="8" cy="8" r="6.5"/><path d="M8 5v3.5l2.5 1.5"/></svg>
            Passive, read-only intelligence — Irochi observes but never modifies network traffic
          </div>
        </div>
      </section>

      {/* Capabilities */}
      <section className="landing-capabilities">
        <h2>Six Threat Detection Capabilities</h2>
        <p className="section-subtitle">
          Irochi identifies six classes of network threats using five specialized detector modules
          analyzing Zeek logs, NetFlow, and IPFIX telemetry.
        </p>
        <div className="capabilities-grid">
          {CAPABILITIES.map((cap) => (
            <div key={cap.title} className="capability-card">
              <span className="capability-icon">{cap.icon}</span>
              <h3>{cap.title}</h3>
              <p>{cap.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Passive Intelligence */}
      <section className="landing-passive">
        <div className="passive-content">
          <h2>Passive by Design</h2>
          <div className="passive-grid">
            <div className="passive-item">
              <span className="passive-marker">01</span>
              <h3>Read-Only Monitoring</h3>
              <p>Irochi never blocks, modifies, or interferes with network traffic. Detection is observation-only.</p>
            </div>
            <div className="passive-item">
              <span className="passive-marker">02</span>
              <h3>No Inline Deployment</h3>
              <p>Operates on mirrored traffic and exported telemetry. Zero impact on network performance.</p>
            </div>
            <div className="passive-item">
              <span className="passive-marker">03</span>
              <h3>Real-Time Streaming</h3>
              <p>Alerts stream to analysts via WebSocket as soon as detectors classify a threat.</p>
            </div>
            <div className="passive-item">
              <span className="passive-marker">04</span>
              <h3>Analyst-First Workflow</h3>
              <p>Security analysts investigate, classify, and close alerts. Irochi provides intelligence, not remediation.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <span>Irochi — SIH26145 — Passive Network Threat Intelligence</span>
      </footer>
    </div>
  );
}
