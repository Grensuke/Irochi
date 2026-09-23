import { useNavigate } from 'react-router-dom';
import type { Alert, Severity } from '@/types';
import { THREAT_LABELS } from '@/types';
import './RelatedAlerts.css';

const SEV_COLORS: Record<Severity, string> = {
  critical: 'var(--severity-critical)', high: 'var(--severity-high)',
  medium: 'var(--severity-medium)', low: 'var(--severity-low)', info: 'var(--severity-info)',
};

interface RelatedAlertsProps { alerts: Alert[]; }

function relativeTime(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

export default function RelatedAlerts({ alerts }: RelatedAlertsProps) {
  const navigate = useNavigate();
  return (
    <div className="related-alerts">
      <div className="related-alerts__title">FROM SAME SOURCE</div>
      {alerts.slice(0, 5).map(a => (
        <div key={a.alert_id} className="related-alerts__row" onClick={() => navigate(`/alerts/${a.alert_id}`)}>
          <span className="related-alerts__sev" style={{ backgroundColor: SEV_COLORS[a.severity] }} />
          <span className="related-alerts__type">{THREAT_LABELS[a.threat_type]}</span>
          <span className="related-alerts__time">{relativeTime(a.created_at)}</span>
          <span className="related-alerts__link">→</span>
        </div>
      ))}
      {alerts.length === 0 && (
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>
          No related alerts found
        </div>
      )}
    </div>
  );
}
