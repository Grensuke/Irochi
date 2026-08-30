import './Capabilities.css';

const DETECTOR_MAPPING = [
  {
    detector: 'DDoS Detector',
    threats: ['Volumetric & Protocol DDoS'],
    desc: 'Analyzes high-volume flow trends and packet frequencies. Flags protocols exhibiting severe payload asymmetry or anomalous packet counts indicating flooding behaviors.',
    signals: ['Packet arrival intervals, TCP packet sizes, byte-to-packet ratios, host-flow counts.'],
    evidence: 'SYN flood pattern match: 42,000 requests observed from a single subnet in a 10s window.'
  },
  {
    detector: 'Recon Detector',
    threats: ['Reconnaissance & Port Scanning'],
    desc: 'Identifies sequential network profiling sweeps and host scans. Detects remote entities probing active subnets or sweeping across connection ports.',
    signals: ['Sequential connection failure rates, host-port distribution metrics, UDP scanning frequencies.'],
    evidence: 'Horizontal port scan targeting internal /24 subnet. 85 failed socket connections.'
  },
  {
    detector: 'DNS/DGA/DNS-Tunneling Detector',
    threats: ['DGA & DNS Tunneling'],
    desc: 'Monitors UDP/53 and TCP/53 lookups. Flags anomalies in domain entropy indicating Algorithmically Generated Domains (DGA) or TXT query size shifts indicating active exfiltration tunnels.',
    signals: ['DNS name character entropy, DNS response sizes, TXT query record ratios, query frequencies.'],
    evidence: 'High entropy DNS TXT query tunnel detected. Query sizes exceed baseline averages by 800%.'
  },
  {
    detector: 'TLS/C2 Detector',
    threats: ['Botnet C2 Beaconing', 'Malware inside encrypted sessions'],
    desc: 'Inspects handshake structures of encrypted TLS connections to expose command-and-control beacons and malware signatures without decrypting payloads.',
    signals: ['Client JA3/JA4 signatures, server certificate validity, packet jitter profiles, periodic connection intervals.'],
    evidence: 'Command & Control beaconing identified. Outbound TLS flows exhibit a strict 30s interval with 0% jitter.'
  },
  {
    detector: 'Exfiltration Detector',
    threats: ['Data Exfiltration'],
    desc: 'Evaluates outbound traffic sizes. Compares transfers against historical baselines of standard internal entities to flag unauthorized payload transfers.',
    signals: ['Unidirectional payload volume, outbound session durations, protocol transfer baselines.'],
    evidence: 'Anomalous outbound transfer of 4.2GB payload. Historical host baseline is 10MB per 24 hours.'
  }
];

export function Capabilities() {
  return (
    <div className="capabilities-page">
      <div className="capabilities-container">
        {/* Header */}
        <section className="cap-header scroll-reveal">
          <div className="section-eyebrow">DETECTION CAPABILITIES</div>
          <h1 className="cap-title">Advanced threat detection.<br />No network write-back.</h1>
          <p className="cap-subtitle">
            Irochi uses five specialized, logical detector modules running on normalized streaming telemetry to identify the six core cyber threat capabilities.
          </p>
        </section>

        {/* Detector Mappings */}
        <section className="detector-section scroll-reveal">
          <div className="detector-section-header">
            <h2 className="section-title-sm">Logical Detector Architecture</h2>
            <div className="detector-arch-note">
              <strong>Architecture Note:</strong> Detectors are logical analysis modules residing in a single pipeline, NOT decoupled microservices. This guarantees low processing latency and prevents synchronization bottlenecks.
            </div>
          </div>

          <div className="detector-list">
            {DETECTOR_MAPPING.map((item) => (
              <div key={item.detector} className="detector-card">
                <div className="detector-card-header">
                  <span className="detector-tag">DETECTOR MODULE</span>
                  <h3 className="detector-name">{item.detector}</h3>
                  <div className="detector-threats">
                    {item.threats.map(t => (
                      <span key={t} className="detector-threat-badge">{t}</span>
                    ))}
                  </div>
                </div>

                <div className="detector-card-body">
                  <p className="detector-desc">{item.desc}</p>
                  
                  <div className="detector-details-grid">
                    <div>
                      <span className="detail-label">INPUT SIGNALS</span>
                      <p className="detail-val">{item.signals}</p>
                    </div>
                    <div>
                      <span className="detail-label">EXAMPLE EVIDENCE MODEL</span>
                      <p className="detail-val mono text-technical">{item.evidence}</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
