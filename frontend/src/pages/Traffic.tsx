import { useState, useEffect } from 'react';
import { Activity, Radio, ActivitySquare, Zap, ShieldAlert, ArrowUpRight } from 'lucide-react';

const PROTOCOLS = [
  { name: 'TCP', color: 'var(--severity-info)', base: 45 },
  { name: 'UDP', color: 'var(--accent-primary)', base: 25 },
  { name: 'TLS', color: 'var(--severity-low)', base: 15 },
  { name: 'DNS', color: 'var(--severity-medium)', base: 8 },
  { name: 'ICMP', color: 'var(--status-investigating)', base: 4 },
  { name: 'QUIC', color: 'var(--severity-high)', base: 3 },
];

export function Traffic() {
  const [totalTraffic, setTotalTraffic] = useState<number[]>(Array.from({ length: 40 }, () => Math.random() * 50 + 50));
  const [threatTraffic, setThreatTraffic] = useState<number[]>(Array.from({ length: 40 }, () => Math.random() * 10 + 2));
  const [protocols, setProtocols] = useState(PROTOCOLS.map(p => ({ ...p, pct: p.base })));

  useEffect(() => {
    const interval = setInterval(() => {
      setTotalTraffic(prev => {
        const next = [...prev.slice(1)];
        const lastValue = prev[prev.length - 1];
        let newValue = lastValue + (Math.random() * 40 - 20);
        if (newValue > 120) newValue = 120;
        if (newValue < 30) newValue = 30;
        next.push(newValue);
        return next;
      });

      setThreatTraffic(prev => {
        const next = [...prev.slice(1)];
        const lastValue = prev[prev.length - 1];
        // Occasional spikes for threats
        const spike = Math.random() > 0.8 ? Math.random() * 30 : (Math.random() * 4 - 2);
        let newValue = lastValue + spike;
        if (newValue > 50) newValue = 50;
        if (newValue < 1) newValue = 1;
        next.push(newValue);
        return next;
      });

      setProtocols(prev => {
        let total = 0;
        const newProtos = prev.map(p => {
          let newPct = p.base + (Math.random() * 4 - 2);
          if (newPct < 0.1) newPct = 0.1;
          total += newPct;
          return { ...p, raw: newPct };
        });
        return newProtos.map(p => ({
          ...p,
          pct: (p.raw / total) * 100
        })).sort((a, b) => b.pct - a.pct);
      });
    }, 1500);

    return () => clearInterval(interval);
  }, []);

  const currentTotal = totalTraffic[totalTraffic.length - 1];
  const currentThreat = threatTraffic[threatTraffic.length - 1];
  const maxTrafficValue = 130;

  // Generate SVG paths
  const generateAreaPath = (data: number[]) => {
    const points = data.map((val, i) => {
      const x = (i / (data.length - 1)) * 100;
      const y = 100 - (val / maxTrafficValue) * 100;
      return `${x},${y}`;
    }).join(' ');
    return {
      line: points,
      area: `0,100 ${points} 100,100`
    };
  };

  const totalPath = generateAreaPath(totalTraffic);
  const threatPath = generateAreaPath(threatTraffic);

  return (
    <div className="traffic-page">
      <div className="page-header" style={{ padding: '0 0 var(--space-4) 0' }}>
        <h1 style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <Activity size={24} style={{ color: 'var(--severity-info)' }} />
          Network Telemetry
        </h1>
        <div className="page-header-actions">
          <span className="phase-badge live">
            <Radio size={12} style={{ marginRight: '4px' }}/> Live Analysis
          </span>
        </div>
      </div>

      <div className="kpi-grid" style={{ marginBottom: 'var(--space-4)' }}>
        <div className="kpi-cell">
          <div className="kpi-label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <ActivitySquare size={14} style={{ color: 'var(--severity-info)' }}/>
            TOTAL INGRESS
          </div>
          <div className="kpi-value">{currentTotal.toFixed(1)} <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>Mbps</span></div>
          <div className="kpi-trend up"><ArrowUpRight size={14} /> +2.4% vs avg</div>
        </div>
        <div className="kpi-cell">
          <div className="kpi-label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Zap size={14} style={{ color: 'var(--severity-medium)' }}/>
            ACTIVE STREAMS
          </div>
          <div className="kpi-value">{Math.floor(currentTotal * 14.2).toLocaleString()}</div>
          <div className="kpi-trend neutral">Stable</div>
        </div>
        <div className="kpi-cell">
          <div className="kpi-label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <ShieldAlert size={14} style={{ color: 'var(--severity-critical)' }}/>
            THREAT LOAD
          </div>
          <div className="kpi-value" style={{ color: currentThreat > 30 ? 'var(--severity-critical)' : 'var(--text-primary)' }}>
            {currentThreat.toFixed(1)} <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>Mbps</span>
          </div>
          <div className="kpi-trend up"><ArrowUpRight size={14} /> Active attacks detected</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: 'var(--space-5)' }}>
        <div className="panel" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="panel-header">
            <span className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Radio size={16} style={{ color: 'var(--severity-info)' }}/> 
              Real-time Throughput Analysis
            </span>
            <div style={{ display: 'flex', gap: 'var(--space-4)', fontSize: '12px' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: 'var(--severity-info)' }}></span>
                Total Traffic
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: 'var(--severity-critical)' }}></span>
                Threat Anomalies
              </span>
            </div>
          </div>
          <div className="panel-body" style={{ flex: 1, padding: '0', position: 'relative', overflow: 'hidden' }}>
            <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: '100%', height: '300px', display: 'block' }}>
              <defs>
                <linearGradient id="totalGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--severity-info)" stopOpacity="0.12"/>
                  <stop offset="100%" stopColor="var(--severity-info)" stopOpacity="0.0"/>
                </linearGradient>
                <linearGradient id="threatGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--severity-critical)" stopOpacity="0.2"/>
                  <stop offset="100%" stopColor="var(--severity-critical)" stopOpacity="0.0"/>
                </linearGradient>
              </defs>
              
              {/* Grid lines */}
              {[25, 50, 75].map(y => (
                <line key={y} x1="0" y1={y} x2="100" y2={y} stroke="var(--border-subtle)" strokeWidth="0.1" />
              ))}

              {/* Total Traffic */}
              <polygon points={totalPath.area} fill="url(#totalGrad)" />
              <polyline points={totalPath.line} fill="none" stroke="var(--severity-info)" strokeWidth="0.25" strokeOpacity="0.8" />
              
              {/* Threat Traffic */}
              <polygon points={threatPath.area} fill="url(#threatGrad)" />
              <polyline points={threatPath.line} fill="none" stroke="var(--severity-critical)" strokeWidth="0.35" strokeOpacity="0.85" />
            </svg>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: 'var(--space-2) var(--space-4)', fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              <span>-60s</span>
              <span>-45s</span>
              <span>-30s</span>
              <span>-15s</span>
              <span>Now</span>
            </div>
          </div>
        </div>

        <div className="panel" style={{ height: '100%' }}>
          <div className="panel-header">
            <span className="panel-title">Protocol Distribution</span>
          </div>
          <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)', paddingTop: 'var(--space-5)' }}>
            {protocols.map(proto => (
              <div key={proto.name} className="protocol-row" style={{ gridTemplateColumns: '60px 1fr 40px' }}>
                <div className="protocol-label">{proto.name}</div>
                <div className="protocol-bar-track" style={{ height: '6px', borderRadius: '3px', background: 'var(--bg-tertiary)' }}>
                  <div 
                    className="protocol-bar-fill" 
                    style={{ 
                      width: `${proto.pct}%`,
                      background: proto.color,
                      height: '100%',
                      borderRadius: '3px'
                    }} 
                  />
                </div>
                <div className="protocol-pct">{proto.pct.toFixed(1)}%</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
