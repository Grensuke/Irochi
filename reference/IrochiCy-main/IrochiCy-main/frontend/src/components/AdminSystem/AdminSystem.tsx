import type { SystemService } from '@/types';
import './AdminSystem.css';

const SERVICES: SystemService[] = [
  { name: 'FastAPI', status: 'healthy', metric: 'Uptime', metricValue: '99.9%', lastChecked: new Date().toISOString() },
  { name: 'PostgreSQL', status: 'healthy', metric: 'Pool Usage', metricValue: '34/100', lastChecked: new Date().toISOString() },
  { name: 'Redis', status: 'healthy', metric: 'Memory', metricValue: '128 MB / 2 GB', lastChecked: new Date().toISOString() },
  { name: 'Redpanda', status: 'healthy', metric: 'Consumer Lag', metricValue: '< 50 msgs', lastChecked: new Date().toISOString() },
  { name: 'Detection Workers', status: 'healthy', metric: 'Active', metricValue: '5 of 5', lastChecked: new Date().toISOString() },
  { name: 'Zeek', status: 'healthy', metric: 'Status', metricValue: 'RUNNING', lastChecked: new Date().toISOString() },
];

const PIPELINE_KPIS = [
  { label: 'Events Ingested', value: '1,247,892' },
  { label: 'Features Computed', value: '892,341' },
  { label: 'Detections Fired', value: '3,421' },
  { label: 'Alerts Created', value: '847' },
];

export default function AdminSystem() {
  return (
    <div>
      <div className="admin-system__title">System Health</div>

      <div className="admin-system__subtitle">SERVICE STATUS</div>
      <div className="admin-system__grid">
        {SERVICES.map(s => (
          <div key={s.name} className="admin-system__card">
            <div className="admin-system__card-header">
              <span className={`admin-system__dot admin-system__dot--${s.status}`} />
              <span className="admin-system__service">{s.name}</span>
            </div>
            <div className="admin-system__metric-label">{s.metric}</div>
            <div className="admin-system__metric-value">{s.metricValue}</div>
            <div className="admin-system__time">Last checked: just now</div>
          </div>
        ))}
      </div>

      <div className="admin-system__subtitle">PIPELINE METRICS (LAST HOUR)</div>
      <div className="admin-system__kpi-grid">
        {PIPELINE_KPIS.map(k => (
          <div key={k.label} className="admin-system__kpi">
            <div className="admin-system__kpi-label">{k.label}</div>
            <div className="admin-system__kpi-value">{k.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
