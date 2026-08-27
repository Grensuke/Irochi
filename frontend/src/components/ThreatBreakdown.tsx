import type { DashboardSummary, ThreatType } from '../types';
import { threatLabel } from '../utils/format';
import { THREAT_TYPE_LABELS } from '../types';
import './ThreatBreakdown.css';

interface ThreatBreakdownProps {
  summary: DashboardSummary | null;
  loading: boolean;
}

const THREAT_COLORS: Record<ThreatType, string> = {
  volumetric_ddos: 'var(--severity-critical)',
  c2_beaconing: 'var(--severity-high)',
  dga_dns_tunnel: 'var(--severity-medium)',
  encrypted_malware: 'var(--accent-purple)',
  recon_portscan: 'var(--accent-primary)',
  data_exfiltration: 'var(--severity-high)',
};

export function ThreatBreakdown({ summary, loading }: ThreatBreakdownProps) {
  if (loading) {
    return (
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title">Threat Categories</span>
        </div>
        <div className="panel-body">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="threat-row">
              <div className="skeleton" style={{ width: '40%', height: 12 }} />
              <div className="skeleton" style={{ width: 30, height: 12 }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!summary) return null;

  const total = summary.total_alerts || 1;
  const threats = Object.keys(THREAT_TYPE_LABELS) as ThreatType[];

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Threat Categories</span>
      </div>
      <div className="panel-body threat-list">
        {threats.map((tt) => {
          const count = summary.by_threat_type[tt] ?? 0;
          const pct = (count / total) * 100;
          return (
            <div key={tt} className="threat-row">
              <div className="threat-info">
                <span className="threat-label">{threatLabel(tt)}</span>
                <span className="threat-count mono">{count}</span>
              </div>
              <div className="threat-bar-track">
                <div
                  className="threat-bar-fill"
                  style={{ width: `${pct}%`, background: THREAT_COLORS[tt] }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
