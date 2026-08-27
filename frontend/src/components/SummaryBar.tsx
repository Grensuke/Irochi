import type { DashboardSummary } from '../types';
import { severityColor } from '../utils/format';
import './SummaryBar.css';

interface SummaryBarProps {
  summary: DashboardSummary | null;
  loading: boolean;
}

export function SummaryBar({ summary, loading }: SummaryBarProps) {
  if (loading) {
    return (
      <div className="summary-bar">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="summary-stat">
            <div className="skeleton" style={{ width: 48, height: 28 }} />
            <div className="skeleton" style={{ width: 60, height: 10, marginTop: 4 }} />
          </div>
        ))}
      </div>
    );
  }

  if (!summary) return null;

  const stats = [
    { label: 'Total Alerts', value: summary.total_alerts, color: 'var(--text-primary)' },
    { label: 'Critical', value: summary.critical_count, color: severityColor('critical') },
    { label: 'High', value: summary.high_count, color: severityColor('high') },
    { label: 'Medium', value: summary.medium_count, color: severityColor('medium') },
    { label: 'Low', value: summary.low_count, color: severityColor('low') },
    { label: 'Info', value: summary.info_count, color: severityColor('info') },
  ];

  return (
    <div className="summary-bar">
      {stats.map((s) => (
        <div key={s.label} className="summary-stat">
          <span className="stat-value" style={{ color: s.color }}>{s.value}</span>
          <span className="stat-label">{s.label}</span>
        </div>
      ))}
    </div>
  );
}
