import { useState, useMemo } from 'react';
import { MOCK_NETWORK_EVENTS } from '../services/mockData';
import type { EventType } from '../types';
import { formatTimestamp, formatDate } from '../utils/format';
import { DiodeFlowVisualizer } from '../components/DiodeFlowVisualizer';
import { useAlerts } from '../hooks/useAlerts';
import './Network.css';

function formatBytes(bytes: number | null): string {
  if (bytes == null) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

interface NetworkGraphProps {
  sources: string[];
  dests: string[];
  connections: Array<{
    id: string;
    src: string;
    dst: string;
    srcIndex: number;
    dstIndex: number;
    protocol: string;
    type: string;
    bytes: number;
  }>;
}

function NetworkGraph({ sources, dests, connections }: NetworkGraphProps) {
  const W = 800;
  const H = 260;

  const getSrcY = (idx: number) => {
    const step = H / (sources.length + 1);
    return step * (idx + 1);
  };

  const getDstY = (idx: number) => {
    const step = H / (dests.length + 1);
    return step * (idx + 1);
  };

  return (
    <div className="panel" style={{ marginBottom: 'var(--space-5)' }}>
      <div className="panel-header">
        <span className="panel-title">Active Connection Topology Map</span>
        <span className="demo-badge">FLOW GRAPH</span>
      </div>
      <div className="panel-body" style={{ position: 'relative', overflowX: 'auto', display: 'flex', justifyContent: 'center' }}>
        {sources.length === 0 ? (
          <div className="state-message" style={{ padding: 'var(--space-6) 0' }}>
            <span className="state-title">No connections to map</span>
          </div>
        ) : (
          <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} style={{ minWidth: 600, maxWidth: 800 }}>
            <defs>
              <linearGradient id="linkGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="var(--accent-primary)" stopOpacity="0.4" />
                <stop offset="100%" stopColor="var(--accent-cyan)" stopOpacity="0.4" />
              </linearGradient>
            </defs>

            {/* Connection Lines */}
            {connections.map((c) => {
              const srcY = getSrcY(c.srcIndex);
              const dstY = getDstY(c.dstIndex);
              const pathD = `M 180 ${srcY} C 400 ${srcY}, 400 ${dstY}, 620 ${dstY}`;
              
              return (
                <g key={c.id}>
                  {/* Base Line */}
                  <path
                    d={pathD}
                    fill="none"
                    stroke="url(#linkGradient)"
                    strokeWidth="1.2"
                    opacity="0.5"
                  />
                  {/* Flow Animation Tracer Overlay */}
                  <path
                    d={pathD}
                    fill="none"
                    stroke="var(--accent-cyan)"
                    strokeWidth="1.5"
                    className="chart-flow-line"
                  />
                </g>
              );
            })}

            {/* Source Node circles */}
            {sources.map((ip, i) => {
              const y = getSrcY(i);
              return (
                <g key={`src-${ip}`} transform={`translate(180, ${y})`}>
                  <circle r="6" fill="var(--bg-elevated)" stroke="var(--accent-primary)" strokeWidth="2" />
                  <circle r="12" fill="var(--accent-primary)" fillOpacity="0.08" className="node-pulse" />
                  <text x="-12" y="4" textAnchor="end" fontSize="10" fill="var(--text-primary)" fontFamily="var(--font-mono)">
                    {ip}
                  </text>
                  <text x="-12" y="-8" textAnchor="end" fontSize="8" fill="var(--text-muted)" fontWeight="600">
                    SRC
                  </text>
                </g>
              );
            })}

            {/* Destination Node circles */}
            {dests.map((ip, i) => {
              const y = getDstY(i);
              return (
                <g key={`dst-${ip}`} transform={`translate(620, ${y})`}>
                  <circle r="6" fill="var(--bg-elevated)" stroke="var(--accent-cyan)" strokeWidth="2" />
                  <circle r="12" fill="var(--accent-cyan)" fillOpacity="0.08" className="node-pulse-slow" />
                  <text x="12" y="4" textAnchor="start" fontSize="10" fill="var(--text-primary)" fontFamily="var(--font-mono)">
                    {ip}
                  </text>
                  <text x="12" y="-8" textAnchor="start" fontSize="8" fill="var(--text-muted)" fontWeight="600">
                    DST
                  </text>
                </g>
              );
            })}
          </svg>
        )}
      </div>
    </div>
  );
}

export function Network() {
  const { alerts } = useAlerts();
  const [vizMode, setVizMode] = useState<'diode' | 'matrix'>('diode');
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

  const graphData = useMemo(() => {
    // Unique source and dest IPs (top 5 for readability)
    const sources = Array.from(new Set(filtered.map(e => e.src_ip))).slice(0, 5);
    const dests = Array.from(new Set(filtered.map(e => e.dst_ip))).slice(0, 5);

    const connections = filtered.map(e => {
      const srcIndex = sources.indexOf(e.src_ip);
      const dstIndex = dests.indexOf(e.dst_ip);
      return {
        id: e.event_id,
        src: e.src_ip,
        dst: e.dst_ip,
        srcIndex,
        dstIndex,
        protocol: e.protocol,
        type: e.event_type,
        bytes: (e.orig_bytes ?? 0) + (e.resp_bytes ?? 0)
      };
    }).filter(c => c.srcIndex !== -1 && c.dstIndex !== -1);

    return { sources, dests, connections };
  }, [filtered]);

  return (
    <div className="network-page" style={{ maxWidth: '1600px', width: '100%', margin: '0 auto' }}>
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
          <DiodeFlowVisualizer alerts={alerts} />
        ) : (
          <NetworkGraph 
            sources={graphData.sources} 
            dests={graphData.dests} 
            connections={graphData.connections} 
          />
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
