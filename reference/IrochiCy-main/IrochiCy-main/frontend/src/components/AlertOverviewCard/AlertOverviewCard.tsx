import type { Alert } from '@/types';
import ThreatTypePill from '@/components/ThreatTypePill/ThreatTypePill';
import ConfidenceBar from '@/components/ConfidenceBar/ConfidenceBar';
import './AlertOverviewCard.css';

interface AlertOverviewCardProps { alert: Alert; }

export default function AlertOverviewCard({ alert }: AlertOverviewCardProps) {
  return (
    <div className="alert-overview">
      <div className="alert-overview__top">
        <div className="alert-overview__top-left">
          <ThreatTypePill type={alert.threat_type} large />
          <span className="alert-overview__threat-name">{alert.threat_name || alert.threat_type}</span>
        </div>
        <div>
          <div className="alert-overview__meta">{new Date(alert.created_at).toISOString().replace('T', ' ').slice(0, 23)} UTC</div>
          <div className="alert-overview__detector">Detector: {alert.detector_id}</div>
        </div>
      </div>

      <div className="alert-overview__ips">
        <span className="alert-overview__ip">{alert.src_ip}</span>
        <span className="alert-overview__arrow">→</span>
        <span className="alert-overview__ip">{alert.dst_ip}</span>
        <span className="alert-overview__proto-pill">{alert.protocol}:{alert.dst_port}</span>
      </div>

      <div className="alert-overview__confidence">
        <div className="alert-overview__confidence-label">DETECTION CONFIDENCE</div>
        <ConfidenceBar value={alert.confidence} large />
      </div>
    </div>
  );
}
