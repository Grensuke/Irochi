import { useState } from 'react';
import type { EventType } from '../types';
import { DiodeFlowVisualizer } from '../components/DiodeFlowVisualizer';
import { PageHeader } from '../components/PageHeader';
import { useLiveTelemetry } from '../hooks/useLiveTelemetry';
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
  
  const { flows: flowsPerSec, throughput: mbps, events } = useLiveTelemetry();

  const filteredEvents = events.filter(ev => {
    if (typeFilter && ev.type !== typeFilter) return false;
    if (search) {
      const s = search.toLowerCase();
      if (!ev.id.toLowerCase().includes(s) && 
          !ev.source.includes(s) && 
          !ev.destination.includes(s) && 
          !ev.connection.includes(s)) {
        return false;
      }
    }
    return true;
  });

  return (
    <div className="network-page">
      <PageHeader 
        title="Network Telemetry" 
        actions={
          <div style={{ display: 'flex', gap: 'var(--space-4)', alignItems: 'center' }}>
            <span className="mono" style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              {flowsPerSec.toLocaleString()} Flows/sec
            </span>
            <span className="mono" style={{ color: 'var(--severity-info)', fontSize: '0.8rem', fontWeight: 'bold' }}>
              {mbps.toFixed(1)} Mbps
            </span>
            <span className="mono" style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              {filteredEvents.length} events buffered
            </span>
          </div>
        }
      />

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
          <DiodeFlowVisualizer realOpticalRate={mbps} />
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
                  <th>Sent (B)</th>
                  <th>Received (B)</th>
                  <th>State</th>
                  <th>Sensor</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvents.map(ev => (
                  <tr key={ev.id}>
                    <td className="mono" style={{ fontSize: '0.7rem' }}>{ev.id.substring(0, 16)}...</td>
                    <td>
                      <span className={`event-type-badge ${ev.type}`}>{ev.type}</span>
                    </td>
                    <td className="mono">{new Date(ev.time).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}</td>
                    <td className="mono">{ev.connection}</td>
                    <td className="mono">{ev.source}</td>
                    <td className="mono">{ev.destination}</td>
                    <td className="mono">{ev.protocol}</td>
                    <td className="mono" style={{ textAlign: 'right' }}>{ev.sent.toLocaleString()}</td>
                    <td className="mono" style={{ textAlign: 'right' }}>{ev.received.toLocaleString()}</td>
                    <td className="mono">{ev.state}</td>
                    <td className="mono">{ev.sensor}</td>
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
