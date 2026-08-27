/**
 * Alerts page — dedicated alert management view.
 *
 * Uses existing Checkpoint 2 dummy FastAPI API where available.
 * Frontend-side mock filtering until final API/filter contracts exist.
 */

import { useState, useMemo } from 'react';
import { useAlerts } from '../hooks/useAlerts';
import type { Alert, Severity, ThreatType, AlertStatus } from '../types';
import { THREAT_TYPE_LABELS, SEVERITY_ORDER, STATUS_LABELS } from '../types';
import { formatTimestamp, formatDate, threatLabel, formatConfidence, confidenceColor } from '../utils/format';
import { AlertDetail } from '../components/AlertDetail';
import './Alerts.css';

export function Alerts() {
  const { alerts, loading, error } = useAlerts();
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState<Severity | ''>('');
  const [threatFilter, setThreatFilter] = useState<ThreatType | ''>('');
  const [statusFilter, setStatusFilter] = useState<AlertStatus | ''>('');
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);

  const filtered = useMemo(() => {
    let result = alerts;
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(a =>
        a.alert_id.toLowerCase().includes(q) ||
        a.src_ip?.toLowerCase().includes(q) ||
        a.dst_ip?.toLowerCase().includes(q) ||
        a.evidence_summary.toLowerCase().includes(q)
      );
    }
    if (severityFilter) result = result.filter(a => a.severity === severityFilter);
    if (threatFilter) result = result.filter(a => a.threat_type === threatFilter);
    if (statusFilter) result = result.filter(a => a.status === statusFilter);
    return result;
  }, [alerts, search, severityFilter, threatFilter, statusFilter]);

  return (
    <div className="alerts-page">
      <div className="page-header">
        <h1>Alerts</h1>
        <div className="page-header-actions">
          <span className="alerts-count mono">{filtered.length} alerts</span>
        </div>
      </div>

      <div className="filter-bar">
        <input
          className="input search-input"
          placeholder="Search alerts by ID, IP, or evidence…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select className="select" value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value as Severity | '')}>
          <option value="">All Severities</option>
          {SEVERITY_ORDER.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
        </select>
        <select className="select" value={threatFilter} onChange={(e) => setThreatFilter(e.target.value as ThreatType | '')}>
          <option value="">All Threat Types</option>
          {(Object.keys(THREAT_TYPE_LABELS) as ThreatType[]).map(t => <option key={t} value={t}>{THREAT_TYPE_LABELS[t]}</option>)}
        </select>
        <select className="select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as AlertStatus | '')}>
          <option value="">All Statuses</option>
          {(Object.keys(STATUS_LABELS) as AlertStatus[]).map(s => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
        </select>
        {(search || severityFilter || threatFilter || statusFilter) && (
          <button className="btn btn-ghost btn-sm" onClick={() => { setSearch(''); setSeverityFilter(''); setThreatFilter(''); setStatusFilter(''); }}>
            Clear
          </button>
        )}
      </div>

      <div className="alerts-body">
        {loading ? (
          <div className="panel" style={{ margin: '0 var(--space-6)' }}>
            <div className="panel-body">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} style={{ padding: 'var(--space-2) 0' }}>
                  <div className="skeleton" style={{ width: '100%', height: 36 }} />
                </div>
              ))}
            </div>
          </div>
        ) : error ? (
          <div className="state-message">
            <svg viewBox="0 0 24 24" fill="none" stroke="var(--status-error)" strokeWidth="2">
              <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span className="state-title">Failed to load alerts</span>
            <span className="state-detail">{error}</span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="state-message">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <span className="state-title">No alerts found</span>
            <span className="state-detail">
              {search || severityFilter || threatFilter || statusFilter
                ? 'Try adjusting your filters.'
                : 'No threat alerts detected.'}
            </span>
          </div>
        ) : (
          <div className="panel alerts-table-panel">
            <div className="alert-table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Severity</th>
                    <th>Time</th>
                    <th>ID</th>
                    <th>Threat Type</th>
                    <th>Confidence</th>
                    <th>Source</th>
                    <th>Destination</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(alert => (
                    <tr
                      key={alert.alert_id}
                      className="alert-row"
                      onClick={() => setSelectedAlert(alert)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === 'Enter' && setSelectedAlert(alert)}
                    >
                      <td><span className={`severity-badge ${alert.severity}`}>{alert.severity}</span></td>
                      <td className="mono">
                        <span className="alert-date">{formatDate(alert.timestamp)}</span>
                        <span className="alert-time">{formatTimestamp(alert.timestamp)}</span>
                      </td>
                      <td className="mono alert-id-cell">{alert.alert_id}</td>
                      <td>{threatLabel(alert.threat_type)}</td>
                      <td>
                        <div className="confidence-cell">
                          <span className="mono">{formatConfidence(alert.confidence)}</span>
                          <div className="confidence-bar">
                            <div className="confidence-fill" style={{ width: `${alert.confidence * 100}%`, background: confidenceColor(alert.confidence) }} />
                          </div>
                        </div>
                      </td>
                      <td className="mono">{alert.src_ip ?? '—'}</td>
                      <td className="mono">{alert.dst_ip ?? '—'}{alert.dst_port ? `:${alert.dst_port}` : ''}</td>
                      <td><span className={`status-text ${alert.status}`}>{STATUS_LABELS[alert.status]}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {selectedAlert && (
        <AlertDetail alert={selectedAlert} onClose={() => setSelectedAlert(null)} />
      )}
    </div>
  );
}
