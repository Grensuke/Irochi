/**
 * AIDetection page.
 *
 * Displays the five logical detector modules (static info cards).
 * IMPORTANT: No precision/recall/F1 or any invented production metrics
 * are shown here. A banner explicitly states that production metrics
 * are not yet available.
 *
 * When real production metrics exist, they will come from the backend API.
 * This page must NOT invent metric values.
 */

import { PageHeader } from '../components/PageHeader';
import './AIDetection.css';

const DETECTOR_MODULES = [
  {
    id: 'ddos',
    label: 'DDoS Detector',
    description:
      'Detects volumetric Denial-of-Service patterns by observing passive traffic flow statistics. Classifies high-volume packet anomalies and SYN flood patterns.',
    threats: ['Volumetric DDoS'],
    method: 'Flow-feature analysis + River online learning',
  },
  {
    id: 'recon',
    label: 'Recon Detector',
    description:
      'Identifies reconnaissance and port-scanning behaviour from passive connection telemetry. Tracks sweep patterns across observed source/destination pairs.',
    threats: ['Recon / Port Scan'],
    method: 'Sliding-window sweep detection + XGBoost classifier',
  },
  {
    id: 'dns',
    label: 'DNS / DGA / Tunneling Detector',
    description:
      'Analyses passive DNS query patterns to detect domain generation algorithm (DGA) activity and DNS-based data tunneling. Operates solely on observed DNS telemetry.',
    threats: ['DGA / DNS Tunnel'],
    method: 'N-gram language model + entropy analysis',
  },
  {
    id: 'tls_c2',
    label: 'TLS / C2 Detector',
    description:
      'Classifies encrypted session metadata to identify botnet Command-and-Control beaconing and malware communication within TLS flows without decrypting payloads.',
    threats: ['C2 Beaconing', 'Encrypted Malware'],
    method: 'TLS metadata features + scikit-learn ensemble',
  },
  {
    id: 'exfil',
    label: 'Exfiltration Detector',
    description:
      'Detects anomalous outbound data volumes that are consistent with data exfiltration. Relies on passive flow-level byte and packet counters.',
    threats: ['Data Exfiltration'],
    method: 'Statistical baseline deviation + River adaptive model',
  },
];

export function AIDetection() {
  return (
    <div className="ai-detection-page">
      <PageHeader title="AI Detection" />

      {/* Production metrics unavailable banner */}
      <div className="ai-unavailable-banner" role="status">
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
        >
          <circle cx="8" cy="8" r="7" />
          <line x1="8" y1="5" x2="8" y2="8" />
          <circle cx="8" cy="11" r="0.6" fill="currentColor" />
        </svg>
        <span>
          <strong>No production metrics available.</strong> Precision, recall, F1,
          and throughput figures will appear here once the production pipeline is
          operational. Values shown below describe module design only.
        </span>
      </div>

      <div className="ai-section-header">
        <p className="ai-section-title">Five Detector Modules</p>
        <p className="ai-section-desc">
          Each module is a logical component of the AI pipeline, not a separate
          microservice. A single detector may classify multiple threat types.
        </p>
      </div>

      {/* Detector module cards */}
      <div className="detector-grid">
        {DETECTOR_MODULES.map((mod) => (
          <div key={mod.id} className="detector-card panel">
            <div className="panel-header">
              <span className="panel-title">{mod.label}</span>
            </div>
            <div className="detector-card-body">
              <p className="detector-description">{mod.description}</p>
              <div className="detector-meta">
                <div className="detector-field">
                  <span className="detail-label">Classified threats</span>
                  <div className="detector-tags">
                    {mod.threats.map((t) => (
                      <span key={t} className="detector-tag">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="detector-field">
                  <span className="detail-label">Detection method</span>
                  <span className="mono detector-method">{mod.method}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
