/**
 * Network / Events page.
 *
 * Shows mock normalized flow/event records.
 * Fields are from docs/data/CANONICAL_EVENT_SCHEMA_FINAL.md ONLY.
 * No derived canonical fields are invented.
 */

import { useState, useMemo } from 'react';
import { MOCK_NETWORK_EVENTS } from '../services/mockData';
import type { EventType } from '../types';
import { formatTimestamp, formatDate } from '../utils/format';
import './Network.css';

function formatBytes(bytes: number | null): string {
  if (bytes == null) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

export function Network() {
  const [typeFilter, setTypeFilter] = useState<EventType | ''>('');
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    let result = MOCK_NETWORK_EVENTS;
    if (typeFilter) result = result.filter(e => e.event_type === typeFilter);
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(e =>
        e.event_id.toLowerCase().includes(q) ||
        e.src_ip.toLowerCase().includes(q) ||
        e.dst_ip.toLowerCase().includes(q) ||
        e.connection_id.toLowerCase().includes(q)
      );
    }
    return result;
  }, [typeFilter, search]);

  return (
    <div className="network-page">
      <div className="page-header">
        <h1>Network Events</h1>
        <div className="page-header-actions">
          <span className="demo-badge">MOCK DATA</span>
          <span className="mono" style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
            {filtered.length} events
          </span>
        </div>
      </div>

      <div className="filter-bar">
        <input
          className="input search-input"
          placeholder="Search by event ID, IP, or connection ID…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select className="select" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value as EventType | '')}>
          <option value="">All Event Types</option>
          <option value="connection">Connection</option>
          <option value="dns">DNS</option>
          <option value="tls">TLS</option>
        </select>
        {(search || typeFilter) && (
          <button className="btn btn-ghost btn-sm" onClick={() => { setSearch(''); setTypeFilter(''); }}>Clear</button>
        )}
      </div>

      <div className="network-body">
        <div className="panel">
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Event ID</th>
                  <th>Type</th>
                  <th>Time</th>
                  <th>Connection</th>
                  <th>Source</th>
                  <th>Destination</th>
                  <th>Protocol</th>
                  <th>Sent</th>
                  <th>Received</th>
                  <th>State</th>
                  <th>Sensor</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(event => (
                  <tr key={event.event_id}>
                    <td className="mono" style={{ color: 'var(--accent-primary)' }}>{event.event_id}</td>
                    <td><span className={`event-type-badge ${event.event_type}`}>{event.event_type}</span></td>
                    <td className="mono">
                      <span className="alert-date">{formatDate(event.timestamp)}</span>
                      <span className="alert-time">{formatTimestamp(event.timestamp)}</span>
                    </td>
                    <td className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{event.connection_id}</td>
                    <td className="mono">{event.src_ip}:{event.src_port}</td>
                    <td className="mono">{event.dst_ip}:{event.dst_port}</td>
                    <td className="mono">{event.protocol}</td>
                    <td className="mono">{formatBytes(event.orig_bytes)}</td>
                    <td className="mono">{formatBytes(event.resp_bytes)}</td>
                    <td className="mono">{event.conn_state ?? '—'}</td>
                    <td style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{event.sensor_source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
