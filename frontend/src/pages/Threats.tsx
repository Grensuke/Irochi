/**
 * Threats / Detection overview page.
 *
 * Shows the six threat capabilities and five detector modules
 * with alert counts from the dashboard API.
 * Detailed theory content is available on the landing page
 * under "More about Irochi".
 */

import { useDashboard } from '../hooks/useDashboard';
import { THREAT_TYPE_LABELS, DETECTOR_LABELS } from '../types';
import type { ThreatType, DetectorId } from '../types';
import './Threats.css';

const DETECTOR_THREAT_MAP: Record<DetectorId, ThreatType[]> = {
  ddos_detector: ['volumetric_ddos'],
  recon_detector: ['recon_portscan'],
  dns_dga_tunnel_detector: ['dga_dns_tunnel'],
  tls_c2_detector: ['c2_beaconing', 'encrypted_malware'],
  exfiltration_detector: ['data_exfiltration'],
  anomaly_detector: ['novel_anomaly'],
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
        <h2 className="section-title">Threat Categories</h2>
        <div className="threats-grid">
          {threatTypes.map(tt => {
            const count = summary?.by_threat_type[tt] ?? 0;
            return (
              <div key={tt} className="threat-card panel">
                <div className="threat-card-header">
                  <span className="threat-card-title">{THREAT_TYPE_LABELS[tt]}</span>
                  <span className="threat-card-count mono">{loading ? '—' : count}</span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Detector Modules */}
      <section className="threats-section">
        <h2 className="section-title">Detector Modules</h2>
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

