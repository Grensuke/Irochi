/**
 * Analytics page.
 *
 * All values displayed are DEMO/MOCK data for presentation purposes only.
 * They do NOT represent real model performance, accuracy, throughput,
 * detection rates, or production metrics.
 */

import { useDashboard } from '../hooks/useDashboard';
import { MOCK_ALERT_TREND, MOCK_SEVERITY_TREND, MOCK_CONFIDENCE_DIST } from '../services/mockData';
import { THREAT_TYPE_LABELS, DETECTOR_LABELS } from '../types';
import type { ThreatType, DetectorId } from '../types';
import './Analytics.css';

export function Analytics() {
  const { summary, loading } = useDashboard();

  const threatTypes = Object.keys(THREAT_TYPE_LABELS) as ThreatType[];
  const detectorIds = Object.keys(DETECTOR_LABELS) as DetectorId[];

  const maxTrend = Math.max(...MOCK_ALERT_TREND.map(d => d.value), 1);
  const maxSev = Math.max(...MOCK_SEVERITY_TREND.map(d => d.critical + d.high + d.medium + d.low), 1);
  const maxConf = Math.max(...MOCK_CONFIDENCE_DIST.map(d => d.count), 1);

  return (
    <div className="analytics-page">
      <div className="page-header">
        <h1>Analytics</h1>
        <span className="demo-badge">DEMO / MOCK DATA</span>
      </div>

      <div className="analytics-grid">
        {/* Alert Trend */}
        <div className="panel analytics-card relative-container">
          <div className="panel-header">
            <span className="panel-title">Alert Trend (7 Day)</span>
            <span className="demo-badge planned-tag">Planned</span>
          </div>
          <div className="panel-body chart-body-relative">
            <div className="bar-chart blurred-chart" style={{ height: 100 }}>
              {MOCK_ALERT_TREND.map(d => (
                <div
                  key={d.label}
                  className="bar-chart-bar"
                  style={{ height: `${(d.value / maxTrend) * 100}%`, background: 'var(--accent-primary)' }}
                >
                  <span className="bar-chart-label">{d.label}</span>
                </div>
              ))}
            </div>
            <div className="chart-planned-overlay">
              <span className="overlay-title">Coming with analytics data</span>
              <span className="overlay-desc">Requires timeseries aggregate endpoints</span>
            </div>
          </div>
        </div>

        {/* Severity Trend */}
        <div className="panel analytics-card relative-container">
          <div className="panel-header">
            <span className="panel-title">Severity Distribution (7 Day)</span>
            <span className="demo-badge planned-tag">Planned</span>
          </div>
          <div className="panel-body chart-body-relative">
            <div className="stacked-chart blurred-chart" style={{ height: 100 }}>
              {MOCK_SEVERITY_TREND.map(d => {
                const total = d.critical + d.high + d.medium + d.low;
                return (
                  <div key={d.label} className="stacked-col" style={{ height: `${(total / maxSev) * 100}%` }}>
                    <div style={{ flex: d.critical, background: 'var(--severity-critical)' }} />
                    <div style={{ flex: d.high, background: 'var(--severity-high)' }} />
                    <div style={{ flex: d.medium, background: 'var(--severity-medium)' }} />
                    <div style={{ flex: d.low, background: 'var(--severity-low)' }} />
                    <span className="bar-chart-label">{d.label}</span>
                  </div>
                );
              })}
            </div>
            <div className="chart-legend blurred-chart">
              <span className="legend-item"><span className="legend-dot" style={{ background: 'var(--severity-critical)' }} />Critical</span>
              <span className="legend-item"><span className="legend-dot" style={{ background: 'var(--severity-high)' }} />High</span>
              <span className="legend-item"><span className="legend-dot" style={{ background: 'var(--severity-medium)' }} />Medium</span>
              <span className="legend-item"><span className="legend-dot" style={{ background: 'var(--severity-low)' }} />Low</span>
            </div>
            <div className="chart-planned-overlay">
              <span className="overlay-title">Coming with analytics data</span>
              <span className="overlay-desc">Requires historical database retention metrics</span>
            </div>
          </div>
        </div>

        {/* Confidence Distribution */}
        <div className="panel analytics-card relative-container">
          <div className="panel-header">
            <span className="panel-title">Confidence Distribution</span>
            <span className="demo-badge planned-tag">Planned</span>
          </div>
          <div className="panel-body chart-body-relative">
            <div className="h-bar-chart blurred-chart">
              {MOCK_CONFIDENCE_DIST.map(d => (
                <div key={d.range} className="h-bar-row">
                  <span className="h-bar-label mono">{d.range}</span>
                  <div className="h-bar-track">
                    <div className="h-bar-fill" style={{ width: `${(d.count / maxConf) * 100}%`, background: 'var(--accent-cyan)' }} />
                  </div>
                  <span className="h-bar-value mono">{d.count}</span>
                </div>
              ))}
            </div>
            <div className="chart-planned-overlay">
              <span className="overlay-title">Coming with analytics data</span>
              <span className="overlay-desc">Requires ML confidence score histogram indexing</span>
            </div>
          </div>
        </div>

        {/* Threat Distribution */}
        <div className="panel analytics-card">
          <div className="panel-header">
            <span className="panel-title">Threat Type Distribution</span>
          </div>
          <div className="panel-body">
            {loading ? (
              <div className="skeleton" style={{ height: 120, width: '100%' }} />
            ) : (
              <div className="h-bar-chart">
                {threatTypes.map(tt => {
                  const count = summary?.by_threat_type[tt] ?? 0;
                  const maxT = Math.max(...threatTypes.map(t => summary?.by_threat_type[t] ?? 0), 1);
                  return (
                    <div key={tt} className="h-bar-row">
                      <span className="h-bar-label">{THREAT_TYPE_LABELS[tt]}</span>
                      <div className="h-bar-track">
                        <div className="h-bar-fill" style={{ width: `${(count / maxT) * 100}%`, background: 'var(--accent-primary)' }} />
                      </div>
                      <span className="h-bar-value mono">{count}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Detector Activity */}
        <div className="panel analytics-card">
          <div className="panel-header">
            <span className="panel-title">Detector Activity</span>
          </div>
          <div className="panel-body">
            {loading ? (
              <div className="skeleton" style={{ height: 100, width: '100%' }} />
            ) : (
              <div className="h-bar-chart">
                {detectorIds.map(did => {
                  const count = summary?.by_detector[did] ?? 0;
                  const maxD = Math.max(...detectorIds.map(d => summary?.by_detector[d] ?? 0), 1);
                  return (
                    <div key={did} className="h-bar-row">
                      <span className="h-bar-label">{DETECTOR_LABELS[did]}</span>
                      <div className="h-bar-track">
                        <div className="h-bar-fill" style={{ width: `${(count / maxD) * 100}%`, background: 'var(--accent-purple)' }} />
                      </div>
                      <span className="h-bar-value mono">{count}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Summary Stats */}
        <div className="panel analytics-card">
          <div className="panel-header">
            <span className="panel-title">Summary</span>
          </div>
          <div className="panel-body analytics-summary">
            <div className="stat">
              <span className="stat-value">{loading ? '—' : summary?.total_alerts ?? 0}</span>
              <span className="stat-label">Total Alerts</span>
            </div>
            <div className="stat">
              <span className="stat-value" style={{ color: 'var(--severity-critical)' }}>{loading ? '—' : summary?.critical_count ?? 0}</span>
              <span className="stat-label">Critical</span>
            </div>
            <div className="stat">
              <span className="stat-value" style={{ color: 'var(--severity-high)' }}>{loading ? '—' : summary?.high_count ?? 0}</span>
              <span className="stat-label">High</span>
            </div>
            <div className="stat">
              <span className="stat-value" style={{ color: 'var(--accent-primary)' }}>6</span>
              <span className="stat-label">Threat Types</span>
            </div>
            <div className="stat">
              <span className="stat-value" style={{ color: 'var(--accent-purple)' }}>5</span>
              <span className="stat-label">Detectors</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
