import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Alert, ThreatType, Severity, WebSocketStatus } from '@/types';
import LiveStatusPill from '@/components/LiveStatusPill/LiveStatusPill';
import './LiveAlertFeed.css';

interface LiveAlertFeedProps {
  alerts: Alert[];
  latestAlert: Alert | null;
  wsStatus: WebSocketStatus;
}

const SEVERITY_COLORS: Record<Severity, string> = {
  critical: 'var(--severity-critical)',
  high: 'var(--severity-high)',
  medium: 'var(--severity-medium)',
  low: 'var(--severity-low)',
  info: 'var(--severity-info)',
};

const THREAT_HEX: Record<ThreatType, { bg: string; text: string }> = {
  ddos:  { bg: 'rgba(255, 59, 92, 0.15)',  text: '#FF3B5C' },
  recon: { bg: 'rgba(255, 122, 47, 0.15)', text: '#FF7A2F' },
  dns:   { bg: 'rgba(167, 139, 250, 0.15)', text: '#A78BFA' },
  tls:   { bg: 'rgba(91, 140, 255, 0.15)', text: '#5B8CFF' },
  exfil: { bg: 'rgba(245, 197, 24, 0.15)', text: '#F5C518' },
};

const THREAT_LABELS: Record<ThreatType, string> = {
  ddos: 'DDoS', recon: 'Recon', dns: 'DNS-DGA', tls: 'TLS-C2', exfil: 'Exfil',
};

function relativeTime(isoDate: string): string {
  const diff = Math.floor((Date.now() - new Date(isoDate).getTime()) / 1000);
  if (diff < 5) return 'just now';
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export default function LiveAlertFeed({ alerts, latestAlert, wsStatus }: LiveAlertFeedProps) {
  const navigate = useNavigate();
  const [newAlertId, setNewAlertId] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Flash new alert
  useEffect(() => {
    if (latestAlert) {
      setNewAlertId(latestAlert.alert_id);
      const timer = setTimeout(() => setNewAlertId(null), 1000);
      return () => clearTimeout(timer);
    }
  }, [latestAlert]);

  // Update relative times
  const [, setTick] = useState(0);
  useEffect(() => {
    const interval = setInterval(() => setTick(t => t + 1), 30000);
    return () => clearInterval(interval);
  }, []);

  const displayAlerts = alerts.slice(0, 20);

  return (
    <div className="live-alert-feed">
      <div className="live-alert-feed__header">
        <span className="live-alert-feed__title">LIVE ALERTS</span>
        <LiveStatusPill status={wsStatus} />
      </div>
      <div className="live-alert-feed__list" ref={listRef}>
        {displayAlerts.map(alert => {
          const sevColor = SEVERITY_COLORS[alert.severity];
          const threatStyle = THREAT_HEX[alert.threat_type];

          return (
            <div
              key={alert.alert_id}
              className={`alert-row ${alert.alert_id === newAlertId ? 'alert-row--new' : ''}`}
              onClick={() => navigate(`/alerts/${alert.alert_id}`)}
            >
              <div className="alert-row__severity-bar" style={{ backgroundColor: sevColor }} />
              <div className="alert-row__content">
                <div className="alert-row__top">
                  <span className="alert-row__severity-badge">
                    <span className="alert-row__severity-dot" style={{ backgroundColor: sevColor }} />
                    {alert.severity.toUpperCase()}
                  </span>
                  <span
                    className="alert-row__threat-pill"
                    style={{ backgroundColor: threatStyle.bg, color: threatStyle.text }}
                  >
                    {THREAT_LABELS[alert.threat_type]}
                  </span>
                </div>
                <div className="alert-row__bottom">
                  <span className="alert-row__ip alert-row__ip--src">{alert.src_ip}</span>
                  <span className="alert-row__arrow">→</span>
                  <span className="alert-row__ip alert-row__ip--dst">{alert.dst_ip}</span>
                  <span className="alert-row__time">{relativeTime(alert.created_at)}</span>
                </div>
              </div>
              <span className="alert-row__chevron">→</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
