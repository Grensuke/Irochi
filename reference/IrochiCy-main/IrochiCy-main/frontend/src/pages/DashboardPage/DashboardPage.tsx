import { useState, useEffect, useMemo } from 'react';
import { useOutletContext } from 'react-router-dom';
import type { Alert, WebSocketStatus, DashboardSummary, TimelineBucket, TopSourceIP, ProtocolBreakdown } from '@/types';
import {
  generateMockDashboardSummary,
  generateMockTimeline,
  generateMockTopIPs,
  generateMockProtocolBreakdown,
} from '@/mocks/mockService';
import KPICard from '@/components/KPICard/KPICard';
import ThreatTimeline from '@/components/ThreatTimeline/ThreatTimeline';
import LiveAlertFeed from '@/components/LiveAlertFeed/LiveAlertFeed';
import DetectorStatus from '@/components/DetectorStatus/DetectorStatus';
import ProtocolDonut from '@/components/ProtocolDonut/ProtocolDonut';
import TopSourceIPs from '@/components/TopSourceIPs/TopSourceIPs';
import './DashboardPage.css';

interface OutletContext {
  wsStatus: WebSocketStatus;
  alerts: Alert[];
  latestAlert: Alert | null;
}

export default function DashboardPage() {
  const { wsStatus, alerts, latestAlert } = useOutletContext<OutletContext>();

  const [summary, setSummary] = useState<DashboardSummary>(generateMockDashboardSummary);
  const [timeline, setTimeline] = useState<TimelineBucket[]>(generateMockTimeline);
  const [topIPs, setTopIPs] = useState<TopSourceIP[]>(generateMockTopIPs);
  const [protocols, setProtocols] = useState<ProtocolBreakdown[]>(generateMockProtocolBreakdown);

  // Refresh dashboard data every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setSummary(generateMockDashboardSummary());
      setTopIPs(generateMockTopIPs());
      setProtocols(generateMockProtocolBreakdown());
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  // Update events/sec every 2 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setSummary(prev => ({
        ...prev,
        eventsPerSec: prev.eventsPerSec + Math.floor((Math.random() - 0.5) * 500),
      }));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  // Detector dot data
  const detectorDots = useMemo(() => {
    const colors: Record<string, string> = {
      ddos: 'var(--threat-ddos)',
      recon: 'var(--threat-recon)',
      dns: 'var(--threat-dns)',
      tls: 'var(--threat-tls)',
      exfil: 'var(--threat-exfil)',
    };
    return summary.detectorStatuses.map(d => ({
      color: colors[d.threatType] || 'var(--accent-primary)',
      active: d.status === 'running',
    }));
  }, [summary.detectorStatuses]);

  // Pipeline latency styling
  const latencyClass = summary.pipelineLatencyMs > 1000
    ? 'kpi-card__value--critical'
    : summary.pipelineLatencyMs > 500
      ? 'kpi-card__value--warning'
      : '';

  return (
    <div className="dashboard">
      {/* ─── Row 1: KPI Strip ─── */}
      <div className="dashboard__kpi-row">
        <KPICard
          label="TOTAL ALERTS TODAY"
          value={summary.totalAlertsToday}
          delta={summary.totalAlertsDelta}
          deltaLabel="vs yesterday"
          deltaDirection={summary.totalAlertsDelta >= 0 ? 'up' : 'down'}
          borderColor={summary.activeThreats > 20 ? 'var(--severity-critical)' : 'var(--accent-primary)'}
        />
        <KPICard
          label="ACTIVE THREATS"
          value={summary.activeThreats}
          delta={summary.activeThreatsDelta}
          deltaLabel="in last 1h"
          deltaDirection={summary.activeThreatsDelta >= 0 ? 'up' : 'down'}
          borderColor="var(--severity-critical)"
        />
        <KPICard
          label="EVENTS / SEC"
          value={summary.eventsPerSec}
          delta={0}
          deltaLabel="current throughput"
          deltaDirection="flat"
          borderColor="var(--accent-primary)"
          showPulse
        />
        <KPICard
          label="DETECTORS ACTIVE"
          value={summary.detectorsActive}
          delta={0}
          deltaLabel="of 5 online"
          deltaDirection="flat"
          borderColor="var(--accent-primary)"
          detectorDots={detectorDots}
        />
        <KPICard
          label="PIPELINE LATENCY"
          value={summary.pipelineLatencyMs}
          delta={0}
          deltaLabel="p95 ingest-to-alert"
          deltaDirection="flat"
          borderColor="var(--accent-primary)"
          suffix="ms"
          valueClassName={latencyClass}
        />
      </div>

      {/* ─── Row 2: Timeline + Live Feed ─── */}
      <div className="dashboard__main-row">
        <ThreatTimeline data={timeline} />
        <LiveAlertFeed alerts={alerts} latestAlert={latestAlert} wsStatus={wsStatus} />
      </div>

      {/* ─── Row 3: Detectors + Protocol + Top IPs ─── */}
      <div className="dashboard__bottom-row">
        <DetectorStatus detectors={summary.detectorStatuses} />
        <ProtocolDonut data={protocols} />
        <TopSourceIPs data={topIPs} />
      </div>
    </div>
  );
}
