import { useState } from 'react';
import type { EventType } from '../types';
import { DiodeFlowVisualizer } from '../components/DiodeFlowVisualizer';
import './Network.css';

function NetworkGraphEmptyState() {
  return (
    <div className="panel" style={{ marginBottom: 'var(--space-5)' }}>
      <div className="panel-header">
        <span className="panel-title">Active Connection Topology Map</span>
      </div>
      <div className="panel-body" style={{ position: 'relative', overflowX: 'auto', display: 'flex', justifyContent: 'center' }}>
        <div className="state-message" style={{ padding: 'var(--space-6) 0', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <span className="state-title" style={{ color: 'var(--text-muted)' }}>No Active Telemetry</span>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>Topology mapping requires raw network flow data ingestion.</span>
        </div>
      </div>
    </div>
  );
}

export function Network() {
  const [vizMode, setVizMode] = useState<'diode' | 'matrix'>('diode');
  const [typeFilter, setTypeFilter] = useState<EventType | ''>('');
  const [search, setSearch] = useState('');

  return (
    <div className="network-page" style={{ maxWidth: '1600px', width: '100%', margin: '0 auto' }}>
      <div className="page-header">
        <h1>Network Events</h1>
        <div className="page-header-actions">
          <span className="mono" style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
            0 events
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
        {/* Visualizer Mode Header & Switcher */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
          <div style={{ display: 'inline-flex', background: 'var(--bg-tertiary)', padding: '3px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <button
              className={`btn btn-sm ${vizMode === 'diode' ? 'btn-primary' : 'btn-ghost'}`}
              style={{ padding: '4px 12px', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}
              onClick={() => setVizMode('diode')}
            >
              ⚡ Diode Simplex Dynamics
            </button>
            <button
              className={`btn btn-sm ${vizMode === 'matrix' ? 'btn-primary' : 'btn-ghost'}`}
              style={{ padding: '4px 12px', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}
              onClick={() => setVizMode('matrix')}
            >
              ☍ Topology Matrix
            </button>
          </div>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            {vizMode === 'diode' ? 'Physical Simplex Optical Tap Layer (Photodiode Isolation)' : 'Source-to-Destination Flow Mapping'}
          </span>
        </div>

        {/* Selected Visualizer */}
        {vizMode === 'diode' ? (
          <DiodeFlowVisualizer />
        ) : (
          <NetworkGraphEmptyState />
        )}

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
                <tr>
                  <td colSpan={11} style={{ textAlign: 'center', padding: 'var(--space-6)', color: 'var(--text-muted)' }}>
                    Raw network event telemetry is not currently persisted by the backend.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
