import type { DetectorStatusInfo, ThreatType } from '@/types';
import './DetectorStatus.css';

interface DetectorStatusProps {
  detectors: DetectorStatusInfo[];
}

const THREAT_COLORS: Record<ThreatType, string> = {
  ddos: '#FF3B5C',
  recon: '#FF7A2F',
  dns: '#A78BFA',
  tls: '#5B8CFF',
  exfil: '#F5C518',
};

function relativeTime(isoDate: string): string {
  const diff = Math.floor((Date.now() - new Date(isoDate).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

export default function DetectorStatus({ detectors }: DetectorStatusProps) {
  return (
    <div className="detector-status">
      <div className="detector-status__title">DETECTOR STATUS</div>
      <div className="detector-status__list">
        {detectors.map(det => (
          <div key={det.id} className="detector-card">
            <div className="detector-card__header">
              <span className="detector-card__name">
                <span className={`detector-card__status-dot detector-card__status-dot--${det.status}`} />
                {det.name}
              </span>
              <span className={`detector-card__status-label detector-card__status-label--${det.status}`}>
                {det.status.toUpperCase()}
              </span>
            </div>
            <div className="detector-card__meta">
              <span>Last: {relativeTime(det.lastDetection)}</span>
              <span>Alerts: {det.alertsToday}</span>
              <div className="detector-card__spark">
                {/* Confidence spark bars (5 bars) */}
                {Array.from({ length: 5 }, (_, i) => {
                  const height = Math.max(3, Math.round(det.confidence * 16 * (0.5 + Math.random() * 0.5)));
                  return (
                    <div
                      key={i}
                      className="detector-card__spark-bar"
                      style={{
                        height: `${height}px`,
                        backgroundColor: THREAT_COLORS[det.threatType],
                        opacity: 0.4 + (i / 5) * 0.6,
                      }}
                    />
                  );
                })}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
