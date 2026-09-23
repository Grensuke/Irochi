import { useState, useEffect, useRef } from 'react';
import type { NetworkFlow, ThreatType } from '@/types';
import { generateNetworkFlows } from '@/mocks/mockService';
import './LiveFlowTable.css';

const THREAT_COLORS: Record<ThreatType | 'normal', string> = {
  ddos: '#FF3B5C', recon: '#FF7A2F', dns: '#A78BFA', tls: '#5B8CFF', exfil: '#F5C518', normal: 'var(--border-default)',
};

type ProtoFilter = 'ALL' | 'TCP' | 'UDP' | 'DNS' | 'TLS';

function formatBytes(b: number): string {
  if (b >= 1048576) return `${(b / 1048576).toFixed(1)}M`;
  if (b >= 1024) return `${(b / 1024).toFixed(0)}K`;
  return `${b}B`;
}

function formatDuration(s: number): string {
  if (s < 1) return `${(s * 1000).toFixed(0)}ms`;
  if (s < 60) return `${s.toFixed(1)}s`;
  return `${(s / 60).toFixed(1)}m`;
}

export default function LiveFlowTable() {
  const [flows, setFlows] = useState<NetworkFlow[]>(() => generateNetworkFlows(30));
  const [protoFilter, setProtoFilter] = useState<ProtoFilter>('ALL');
  const [autoScroll, setAutoScroll] = useState(true);
  const [newIds, setNewIds] = useState<Set<string>>(new Set());
  const scrollRef = useRef<HTMLDivElement>(null);

  // Generate new flows every 2s
  useEffect(() => {
    const interval = setInterval(() => {
      const newFlows = generateNetworkFlows(5 + Math.floor(Math.random() * 8));
      setNewIds(new Set(newFlows.map(f => f.id)));
      setFlows(prev => [...newFlows, ...prev].slice(0, 100));
      setTimeout(() => setNewIds(new Set()), 300);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [flows, autoScroll]);

  const filtered = protoFilter === 'ALL'
    ? flows
    : flows.filter(f => {
      if (protoFilter === 'DNS') return f.protocol === 'UDP' && f.dst_port === 53;
      if (protoFilter === 'TLS') return f.protocol === 'TCP' && (f.dst_port === 443 || f.dst_port === 8443);
      return f.protocol === protoFilter;
    });

  const now = Date.now();

  return (
    <div className="flow-table">
      <div className="flow-table__header">
        <span className="flow-table__title">LIVE FLOW TABLE</span>
        <div className="flow-table__controls">
          <div className="flow-table__proto-pills">
            {(['ALL', 'TCP', 'UDP', 'DNS', 'TLS'] as ProtoFilter[]).map(p => (
              <button
                key={p}
                className={`flow-table__proto-pill ${protoFilter === p ? 'flow-table__proto-pill--active' : ''}`}
                onClick={() => setProtoFilter(p)}
              >{p}</button>
            ))}
          </div>
          <button
            className={`flow-table__scroll-toggle ${autoScroll ? 'flow-table__scroll-toggle--on' : ''}`}
            onClick={() => setAutoScroll(v => !v)}
          >📌 AUTO-SCROLL</button>
        </div>
      </div>
      <div className="flow-table__wrap" ref={scrollRef}>
        <table className="flow-table__table">
          <thead>
            <tr>
              <th style={{ width: 60 }}>TIME</th>
              <th style={{ width: 130 }}>SRC IP:PORT</th>
              <th style={{ width: 20 }}></th>
              <th style={{ width: 130 }}>DST IP:PORT</th>
              <th style={{ width: 40 }}>PROTO</th>
              <th style={{ width: 60 }}>BYTES↑</th>
              <th style={{ width: 60 }}>BYTES↓</th>
              <th style={{ width: 60 }}>DURATION</th>
              <th style={{ width: 50 }}>STATE</th>
              <th style={{ width: 50 }}>TYPE</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(f => {
              const age = now - new Date(f.timestamp).getTime();
              const isOld = age > 60000;
              const isNew = newIds.has(f.id);
              const color = THREAT_COLORS[f.event_type];

              return (
                <tr
                  key={f.id}
                  className={`flow-table__row ${isNew ? 'flow-table__row--new' : ''} ${isOld ? 'flow-table__row--old' : ''}`}
                >
                  <td>
                    <span className="flow-table__type-bar" style={{ backgroundColor: color }} />
                    {new Date(f.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </td>
                  <td>{f.src_ip}:{f.src_port}</td>
                  <td style={{ color: 'var(--text-tertiary)', textAlign: 'center' }}>→</td>
                  <td>{f.dst_ip}:{f.dst_port}</td>
                  <td>{f.protocol}</td>
                  <td>{formatBytes(f.bytes_sent)}</td>
                  <td>{formatBytes(f.bytes_recv)}</td>
                  <td>{formatDuration(f.duration)}</td>
                  <td>{f.conn_state}</td>
                  <td style={{ color: f.event_type !== 'normal' ? color : 'var(--text-secondary)', fontWeight: f.event_type !== 'normal' ? 600 : 400 }}>
                    {f.event_type === 'normal' ? '—' : f.event_type.toUpperCase()}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
