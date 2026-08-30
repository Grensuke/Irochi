import type { ReactNode } from 'react';

interface KPIMetricProps {
  label: string;
  value: ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  loading?: boolean;
}

export function KPIMetric({ label, value, trend, trendValue, loading }: KPIMetricProps) {
  if (loading) {
    return (
      <div className="kpi-cell">
        <div className="skeleton" style={{ width: 60, height: 12, marginBottom: 4 }} />
        <div className="skeleton" style={{ width: 40, height: 24 }} />
      </div>
    );
  }

  return (
    <div className="kpi-cell">
      <span className="kpi-label">{label}</span>
      <span className="kpi-value">{value}</span>
      {trendValue && (
        <span className={`kpi-trend ${trend ?? 'neutral'}`}>
          {trend === 'up' && '↑ '}
          {trend === 'down' && '↓ '}
          {trendValue}
        </span>
      )}
    </div>
  );
}
