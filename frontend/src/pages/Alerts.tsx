import { useState, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAlerts } from '../hooks/useAlerts';
import type { Severity, ThreatType, AlertStatus } from '../types';
import { THREAT_TYPE_LABELS, SEVERITY_ORDER, STATUS_LABELS, DETECTOR_LABELS } from '../types';
import { formatTimestamp, threatLabel, formatConfidence, confidenceColor } from '../utils/format';
import { PageHeader } from '../components/PageHeader';
import './Alerts.css';

export function Alerts() {
  const { alerts, loading, error } = useAlerts();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState<Severity | ''>('');
  const [threatFilter, setThreatFilter] = useState<ThreatType | ''>('');
  const [statusFilter, setStatusFilter] = useState<AlertStatus | ''>('');

  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  useEffect(() => {
    setCurrentPage(1);
  }, [search, severityFilter, threatFilter, statusFilter]);

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

  const totalPages = Math.max(Math.ceil(filtered.length / pageSize), 1);

  const paginated = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    return filtered.slice(start, end);
  }, [filtered, currentPage, pageSize]);

  return (
    <div className="alerts-page">
      <PageHeader 
        title="Alerts" 
        actions={<span className="alerts-count mono">{filtered.length} alerts</span>} 
      />

      <div className="filter-bar">
        <input
          className="input search-input"
          placeholder="Search alert ID, IP, flow ID..."
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
                    <th>Time</th>
                    <th>Alert ID</th>
                    <th>Severity</th>
                    <th>Threat</th>
                    <th>Source</th>
                    <th>Destination</th>
                    <th>Detector</th>
                    <th>Confidence</th>
                    <th>Status</th>
                    <th>Phase</th>
                  </tr>
                </thead>
                <tbody>
                  {paginated.map(alert => (
                    <tr
                      key={alert.alert_id}
                      className="alert-row"
                      onClick={() => navigate(`/app/alerts/${alert.alert_id}`)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === 'Enter' && navigate(`/app/alerts/${alert.alert_id}`)}
                    >
                      <td className="mono" style={{ whiteSpace: 'nowrap' }}>
                        <span className="alert-time">{formatTimestamp(alert.timestamp)}</span>
                      </td>
                      <td className="mono alert-id-cell">{alert.alert_id}</td>
                      <td><span className={`severity-badge ${alert.severity}`}>{alert.severity}</span></td>
                      <td>{threatLabel(alert.threat_type)}</td>
                      <td className="mono">{alert.src_ip ?? '—'}</td>
                      <td className="mono">{alert.dst_ip ?? '—'}{alert.dst_port ? `:${alert.dst_port}` : ''}</td>
                      <td className="mono" style={{ color: 'var(--text-technical)' }}>{DETECTOR_LABELS[alert.detector_id]}</td>
                      <td>
                        <span className="mono" style={{ color: confidenceColor(alert.confidence) }}>
                          {formatConfidence(alert.confidence)}
                        </span>
                      </td>
                      <td><span className={`status-text ${alert.status}`}>{STATUS_LABELS[alert.status]}</span></td>
                      <td><span className="phase-badge backfill">Backfilled</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="pagination-bar">
              <span className="pagination-info">
                Browsing loaded alerts: <span className="mono">{filtered.length > 0 ? Math.min((currentPage - 1) * pageSize + 1, filtered.length) : 0}</span>–
                <span className="mono">{Math.min(currentPage * pageSize, filtered.length)}</span> of <span className="mono">{filtered.length}</span>
              </span>

              <div className="pagination-controls">
                <div className="page-size-selector">
                  <label htmlFor="page-size-select">Per page:</label>
                  <select
                    id="page-size-select"
                    className="select select-sm select-page-size"
                    value={pageSize}
                    onChange={(e) => {
                      setPageSize(Number(e.target.value));
                      setCurrentPage(1);
                    }}
                  >
                    <option value={10}>10</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                  </select>
                </div>

                <button
                  className="btn btn-ghost btn-sm"
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                  aria-label="Previous page"
                >
                  Prev
                </button>
                
                <span className="page-indicator">
                  <span className="mono">{currentPage}</span> / <span className="mono">{totalPages}</span>
                </span>

                <button
                  className="btn btn-ghost btn-sm"
                  disabled={currentPage === totalPages}
                  onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                  aria-label="Next page"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
