/**
 * AIDetection page.
 *
 * Displays the five logical detector modules as operational status cards.
 * Detailed descriptions and methods are available on the landing page
 * under "More about Vibhinetra".
 *
 * IMPORTANT: No precision/recall/F1 or any invented production metrics
 * are shown here. A banner explicitly states that production metrics
 * are not yet available.
 */

import { PageHeader } from '../components/PageHeader';
import './AIDetection.css';

const DETECTOR_MODULES = [
  {
    id: 'ddos',
    label: 'DDoS Detector',
    threats: ['Volumetric DDoS'],
  },
  {
    id: 'recon',
    label: 'Recon Detector',
    threats: ['Recon / Port Scan'],
  },
  {
    id: 'dns',
    label: 'DNS / DGA / Tunneling Detector',
    threats: ['DGA / DNS Tunnel'],
  },
  {
    id: 'tls_c2',
    label: 'TLS / C2 Detector',
    threats: ['C2 Beaconing', 'Encrypted Malware'],
  },
  {
    id: 'exfil',
    label: 'Exfiltration Detector',
    threats: ['Data Exfiltration'],
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
          operational.
        </span>
      </div>

      <div className="ai-section-header">
        <p className="ai-section-title">Detector Modules</p>
      </div>

      {/* Detector module cards */}
      <div className="detector-grid">
        {DETECTOR_MODULES.map((mod) => (
          <div key={mod.id} className="detector-card panel">
            <div className="panel-header">
              <span className="panel-title">{mod.label}</span>
            </div>
            <div className="detector-card-body">
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
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

