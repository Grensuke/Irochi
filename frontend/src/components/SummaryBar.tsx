import { useState, useEffect } from 'react';
import type { DashboardSummary } from '../types';
import { KPIMetric } from './KPIMetric';
import './SummaryBar.css';

interface SummaryBarProps {
  summary: DashboardSummary | null;
  loading: boolean;
}

export function SummaryBar({ summary, loading }: SummaryBarProps) {
  const [flows, setFlows] = useState(14502);
  const [throughput, setThroughput] = useState(48.2);
  const [latency, setLatency] = useState(12.4);

  useEffect(() => {
    const interval = setInterval(() => {
      setFlows(prev => prev + Math.floor(Math.random() * 400 - 200));
      setThroughput(prev => Math.max(10, prev + (Math.random() * 8 - 4)));
      setLatency(prev => Math.max(2, prev + (Math.random() * 2 - 1)));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

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
          value={flows.toLocaleString()}
          trend="neutral"
          trendValue="Stable"
          loading={loading}
        />
        <KPIMetric 
          label="Throughput" 
          value={`${throughput.toFixed(1)} Mbps`}
          trend="up"
          trendValue="+1.2%"
          loading={loading}
        />
        <KPIMetric 
          label="Detection Latency" 
          value={`${latency.toFixed(1)} ms`}
          trend="down"
          trendValue="-0.4ms"
          loading={loading}
        />
      </div>
    </div>
  );
}
