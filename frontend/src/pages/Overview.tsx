/**
 * Overview (SOC Dashboard) page.
 * Dark operations-console aesthetic, high density, SVG-based charts.
 */

import { useDashboard } from '../hooks/useDashboard';
import { useAlerts } from '../hooks/useAlerts';
import { useLiveAlerts } from '../hooks/useLiveAlerts';
import { SummaryBar } from '../components/SummaryBar';
import { RecentAlerts } from '../components/RecentAlerts';
import { ThreatBreakdown } from '../components/ThreatBreakdown';
import { LiveFeed } from '../components/LiveFeed';
import { DetectorHealth } from '../components/DetectorHealth';
import { ThreatTimeline } from '../components/ThreatTimeline';
import { formatTimestamp } from '../utils/format';
import './Overview.css';

export function Overview() {
  const { summary, loading: summaryLoading } = useDashboard();
  const { alerts, loading: alertsLoading } = useAlerts();
  const { liveAlerts, connectionState } = useLiveAlerts();

  return (
    <div className="overview-page">
      <div className="section-heading" style={{ margin: 'var(--space-5) var(--space-6) 0', paddingBottom: 'var(--space-2)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: 600, margin: 0, color: 'var(--text-primary)' }}>Overview</h1>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>Passive network intelligence across the monitored environment.</p>
          </div>
          <span className="mono" style={{ fontSize: '11px', color: 'var(--text-muted)', paddingTop: '6px' }}>
            Last updated: {formatTimestamp(new Date().toISOString())} UTC
          </span>
        </div>
      </div>

      <div className="overview-grid">
        <div className="grid-span-12">
          <SummaryBar summary={summary} loading={summaryLoading} />
        </div>

        {/* Row 2: Volume Timeline (8) + Severity breakdown (4) */}
        <div className="grid-span-8">
          <ThreatTimeline />
        </div>
        <div className="grid-span-4">
          <ThreatBreakdown summary={summary} loading={summaryLoading} />
        </div>

        {/* Row 3: Triage Queue (5) + Live Feed (7) */}
        <div className="grid-span-5">
          <RecentAlerts alerts={alerts} loading={alertsLoading} />
        </div>
        <div className="grid-span-7">
          <LiveFeed liveAlerts={liveAlerts} connectionState={connectionState} />
        </div>

        {/* Row 4: Health status (12) */}
        <div className="grid-span-12">
          <DetectorHealth />
        </div>
      </div>
    </div>
  );
}
