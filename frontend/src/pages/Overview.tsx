/**
 * Overview (SOC Dashboard) page.
 *
 * Refactored from the original App.tsx dashboard.
 * Reuses existing components: SummaryBar, AlertTable, ThreatBreakdown, LiveFeed.
 */

import { useDashboard } from '../hooks/useDashboard';
import { useAlerts } from '../hooks/useAlerts';
import { useLiveAlerts } from '../hooks/useLiveAlerts';
import { SummaryBar } from '../components/SummaryBar';
import { AlertTable } from '../components/AlertTable';
import { ThreatBreakdown } from '../components/ThreatBreakdown';
import { LiveFeed } from '../components/LiveFeed';
import './Overview.css';

export function Overview() {
  const { summary, loading: summaryLoading, error: summaryError } = useDashboard();
  const { alerts, loading: alertsLoading, error: alertsError } = useAlerts();
  const { liveAlerts, connectionState } = useLiveAlerts();

  return (
    <div className="overview-page">
      <SummaryBar summary={summary} loading={summaryLoading} />

      {summaryError && (
        <div className="global-error">
          <span>⚠ Dashboard data unavailable: {summaryError}</span>
        </div>
      )}

      <div className="overview-layout">
        <section className="overview-main">
          <AlertTable
            alerts={alerts}
            loading={alertsLoading}
            error={alertsError}
            title="Recent Alerts"
          />
        </section>

        <aside className="overview-sidebar">
          <div className="sidebar-section">
            <ThreatBreakdown summary={summary} loading={summaryLoading} />
          </div>
          <div className="sidebar-section sidebar-feed">
            <LiveFeed liveAlerts={liveAlerts} connectionState={connectionState} />
          </div>
        </aside>
      </div>
    </div>
  );
}
