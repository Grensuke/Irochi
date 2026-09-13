import type { DashboardSummary } from '../types';
import { KPIMetric } from './KPIMetric';
import './SummaryBar.css';

interface SummaryBarProps {
  summary: DashboardSummary | null;
  loading: boolean;
}

export function SummaryBar({ summary, loading }: SummaryBarProps) {
  return (
    <div className="dashboard-kpi">
      <div className="kpi-grid">
        <KPIMetric 
          label="Active Alerts" 
          value={summary?.total_alerts ?? 0} 
          loading={loading}
        />
        <KPIMetric 
          label="Critical" 
          value={summary?.critical_count ?? 0} 
          trend={summary && summary.critical_count > 0 ? 'up' : 'neutral'}
          trendValue={summary && summary.critical_count > 0 ? '+2' : ''}
          loading={loading}
        />
        <KPIMetric 
          label="High" 
          value={summary?.high_count ?? 0} 
          loading={loading}
        />
        <KPIMetric 
          label="Flows / Sec" 
          value="Telemetry unavailable"
          trend="neutral"
          trendValue=""
          loading={loading}
        />
        <KPIMetric 
          label="Throughput" 
          value="Telemetry unavailable"
          trend="neutral"
          trendValue=""
          loading={loading}
        />
        <KPIMetric 
          label="Detection Latency" 
          value="Not measured"
          trend="neutral"
          trendValue=""
          loading={loading}
        />
      </div>
    </div>
  );
}
