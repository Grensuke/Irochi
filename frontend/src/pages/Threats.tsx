/**
 * Threats / Detection overview page.
 *
 * Shows the six threat capabilities and five detector modules.
 * Uses dashboard summary API for counts, with mock trend/evidence data.
 */

import { useDashboard } from '../hooks/useDashboard';
import { THREAT_TYPE_LABELS, DETECTOR_LABELS } from '../types';
import type { ThreatType, DetectorId } from '../types';
import './Threats.css';

const THREAT_DETAILS: Record<ThreatType, { description: string; indicators: string[] }> = {
  volumetric_ddos: {
    description: 'Detection of distributed denial-of-service attacks through traffic volume and protocol anomaly analysis.',
    indicators: ['SYN flood patterns', 'Abnormal packet rates', 'Source entropy elevation', 'Protocol ratio anomalies'],
  },
  c2_beaconing: {
    description: 'Identification of command-and-control communication patterns from compromised hosts.',
    indicators: ['Periodic connection patterns', 'Low-volume persistent flows', 'Unusual destination diversity', 'Timing regularity'],
  },
  dga_dns_tunnel: {
    description: 'Detection of algorithmically generated domains and covert DNS tunneling channels.',
    indicators: ['High-entropy domain names', 'Abnormal DNS query volume', 'Large TXT record responses', 'NXDOMAIN ratios'],
  },
  encrypted_malware: {
    description: 'Identification of malicious payloads hidden within encrypted TLS sessions using metadata analysis.',
    indicators: ['JA3/JA4 fingerprint anomalies', 'Certificate irregularities', 'Unusual TLS version usage', 'Flow size patterns'],
  },
  recon_portscan: {
    description: 'Detection of network reconnaissance activities and systematic port scanning.',
    indicators: ['Sequential port access', 'High destination port diversity', 'Failed connection ratios', 'Sweep patterns'],
  },
  data_exfiltration: {
    description: 'Identification of unauthorized data transfers and anomalous outbound traffic patterns.',
    indicators: ['Unusual outbound volume', 'Off-hours data transfers', 'Asymmetric flow ratios', 'Rare destination IPs'],
  },
};

const DETECTOR_THREAT_MAP: Record<DetectorId, ThreatType[]> = {
  ddos_detector: ['volumetric_ddos'],
  recon_detector: ['recon_portscan'],
  dns_dga_tunnel_detector: ['dga_dns_tunnel'],
  tls_c2_detector: ['c2_beaconing', 'encrypted_malware'],
  exfiltration_detector: ['data_exfiltration'],
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'var(--severity-critical)',
  high: 'var(--severity-high)',
  medium: 'var(--severity-medium)',
  low: 'var(--severity-low)',
};

export function Threats() {
  const { summary, loading } = useDashboard();

  const threatTypes = Object.keys(THREAT_TYPE_LABELS) as ThreatType[];
  const detectorIds = Object.keys(DETECTOR_LABELS) as DetectorId[];

  return (
    <div className="threats-page">
      <div className="page-header">
        <h1>Threats &amp; Detections</h1>
        <span className="demo-badge">DEMO DATA</span>
      </div>

      {/* Threat Capabilities */}
      <section className="threats-section">
        <h2 className="section-title">Six Threat Capabilities</h2>
        <div className="threats-grid">
          {threatTypes.map(tt => {
            const count = summary?.by_threat_type[tt] ?? 0;
            const detail = THREAT_DETAILS[tt];
            return (
              <div key={tt} className="threat-card panel">
                <div className="threat-card-header">
                  <span className="threat-card-title">{THREAT_TYPE_LABELS[tt]}</span>
                  <span className="threat-card-count mono">{loading ? '—' : count}</span>
                </div>
                <p className="threat-card-desc">{detail.description}</p>
                <div className="threat-card-indicators">
                  <span className="indicators-label">Key Indicators</span>
                  <ul>
                    {detail.indicators.map(ind => (
                      <li key={ind}>{ind}</li>
                    ))}
                  </ul>
                </div>
                <div className="threat-card-bar">
                  {['critical', 'high', 'medium', 'low'].map(sev => (
                    <div key={sev} className="mini-sev" style={{ background: SEVERITY_COLORS[sev], opacity: count > 0 ? 1 : 0.2 }} title={sev} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Detector Modules */}
      <section className="threats-section">
        <h2 className="section-title">Five Detector Modules</h2>
        <p className="section-desc">
          Detectors are logical modules, not separate microservices. A detector may produce alerts for multiple threat types.
        </p>
        <div className="detectors-grid">
          {detectorIds.map(did => {
            const count = summary?.by_detector[did] ?? 0;
            const threats = DETECTOR_THREAT_MAP[did];
            return (
              <div key={did} className="detector-card panel">
                <div className="panel-header">
                  <span className="panel-title">{DETECTOR_LABELS[did]}</span>
                  <span className="mono" style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{loading ? '—' : `${count} alerts`}</span>
                </div>
                <div className="panel-body">
                  <div className="detector-threats">
                    {threats.map(tt => (
                      <span key={tt} className="detector-threat-tag">{THREAT_TYPE_LABELS[tt]}</span>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
