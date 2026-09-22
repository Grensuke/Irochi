import { useState, useEffect } from 'react';
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

// Mock event generator for the demo
function generateMockEvent(id: number) {
  const types: EventType[] = ['connection', 'dns', 'tls'];
  const type = types[Math.floor(Math.random() * types.length)];
  const protocols = type === 'connection' ? ['TCP', 'UDP'] : type === 'dns' ? ['UDP'] : ['TCP'];
  const protocol = protocols[Math.floor(Math.random() * protocols.length)];
  
  const srcIp = `10.0.${Math.floor(Math.random() * 5)}.${Math.floor(Math.random() * 254) + 1}`;
  const dstIp = `198.51.100.${Math.floor(Math.random() * 254) + 1}`;
  const srcPort = Math.floor(Math.random() * 50000) + 1024;
  const dstPort = type === 'dns' ? 53 : type === 'tls' ? 443 : Math.floor(Math.random() * 1000);

  return {
    id: `evt_${Date.now()}_${id}`,
    type,
    time: new Date().toISOString(),
    connection: `${srcIp}:${srcPort} ➔ ${dstIp}:${dstPort}`,
    source: srcIp,
    destination: dstIp,
    protocol,
    sent: Math.floor(Math.random() * 5000) + 64,
    received: Math.floor(Math.random() * 50000) + 128,
    state: type === 'connection' ? (Math.random() > 0.8 ? 'S0' : 'SF') : '-',
    sensor: 'vibhinetra-tap-01'
  };
}

export function Network() {
  const [vizMode, setVizMode] = useState<'diode' | 'matrix'>('diode');
  const [typeFilter, setTypeFilter] = useState<EventType | ''>('');
  const [search, setSearch] = useState('');
  
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    // Initial batch
    const initialEvents = Array.from({ length: 15 }, (_, i) => generateMockEvent(i)).reverse();
    setEvents(initialEvents);

    let counter = 100;
    const interval = setInterval(() => {
      const numNew = Math.floor(Math.random() * 3) + 1; // 1 to 3 new events
      const newEvents = Array.from({ length: numNew }, (_, i) => generateMockEvent(counter + i));
      counter += numNew;
      
      setEvents(prev => {
        const next = [...newEvents.reverse(), ...prev];
        return next.slice(0, 30); // Keep max 30 events
      });
    }, 1500);

    return () => clearInterval(interval);
  }, []);

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
    <div className="network-page" style={{ maxWidth: '1600px', width: '100%', margin: '0 auto' }}>
      <div className="page-header">
        <h1>Network Events</h1>
        <div className="page-header-actions">
          <span className="mono" style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
            {filteredEvents.length} events
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
