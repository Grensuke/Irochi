import type { DashboardSummary } from '../types';
import { KPIMetric } from './KPIMetric';
import { useLiveTelemetry } from '../hooks/useLiveTelemetry';
import './SummaryBar.css';

interface SummaryBarProps {
  summary: DashboardSummary | null;
  loading: boolean;
}

export function SummaryBar({ summary, loading }: SummaryBarProps) {
  const { flows, throughput } = useLiveTelemetry();
  const latency = 11.9; // Latency is mostly static for demo

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
          trendValue={summary && summary.critical_count > 0 ? `Active` : ''}
          loading={loading}
        />
        <KPIMetric 
          label="High" 
          value={summary?.high_count ?? 0} 
          loading={loading}
        />
        <KPIMetric 
          label="Flows / Sec" 
          value={flows.toLocaleString()}
          trend="neutral"
          trendValue="Live"
          loading={loading}
        />
        <KPIMetric 
          label="Throughput" 
          value={`${throughput.toFixed(1)} Mbps`}
          trend="neutral"
          trendValue="Live"
          loading={loading}
        />
        <KPIMetric 
          label="Detection Latency" 
          value={`${latency.toFixed(1)} ms`}
          trend="neutral"
          trendValue="Avg"
          loading={loading}
        />
      </div>
    </div>
  );
}
