/**
 * UnidirectionalThreatStream — Hero Visualization
 *
 * Communicates: NETWORK TELEMETRY → SIGNAL EXTRACTION → EVIDENCE CORRELATION → THREAT DETECTION
 */

import { useState, useEffect } from 'react';
import './UnidirectionalThreatStream.css';

interface StreamData {
  id: string;
  ip: string;
  signal: string;
  desc: string;
  observed: string;
  isActive: boolean;
  color: string;
}

const INITIAL_STREAMS: StreamData[] = [
  { id: 's1', ip: '10.0.3.42', signal: 'DNS ANOMALY', desc: 'Repeated encoded DNS requests', observed: 'elevated query frequency', isActive: false, color: 'var(--uts-cyan)' },
  { id: 's2', ip: '192.168.24.17', signal: 'FLOW SPIKE', desc: 'Sudden increase in traffic volume', observed: 'anomalous byte count', isActive: false, color: 'var(--uts-warn)' },
  { id: 's3', ip: '172.16.4.8', signal: 'TLS PATTERN', desc: 'Unusual encrypted traffic signature', observed: 'suspicious JA3 hash', isActive: false, color: 'var(--uts-blue)' },
  { id: 's4', ip: '10.0.8.21', signal: 'SUSPICIOUS DEST', desc: 'Connection to known malicious infrastructure', observed: 'threat intel match', isActive: false, color: 'var(--uts-critical)' },
];

export function UnidirectionalThreatStream() {
  const [streams, setStreams] = useState(INITIAL_STREAMS);
  const [engineState, setEngineState] = useState<'idle' | 'correlating' | 'correlated'>('idle');
  const [cyclePhase, setCyclePhase] = useState(0);

  // Master animation loop
  useEffect(() => {
    let isMounted = true;
    const sequence = async () => {
      // 0: Idle
      if (!isMounted) return;
      setEngineState('idle');
      setStreams(s => s.map(str => ({ ...str, isActive: false })));
      await new Promise(r => setTimeout(r, 1500));

      // 1: Signals start activating
      if (!isMounted) return;
      setStreams(s => s.map((str, i) => i % 2 === 0 ? { ...str, isActive: true } : str));
      await new Promise(r => setTimeout(r, 800));

      // 2: More signals
      if (!isMounted) return;
      setStreams(s => s.map(str => ({ ...str, isActive: true })));
      setEngineState('correlating');
      await new Promise(r => setTimeout(r, 1200));

      // 3: Correlated
      if (!isMounted) return;
      setEngineState('correlated');
      await new Promise(r => setTimeout(r, 4500));
      
      // Loop
      if (!isMounted) return;
      setCyclePhase(p => p + 1);
    };
    sequence();
    return () => { isMounted = false; };
  }, [cyclePhase]);

  const activeCount = streams.filter(s => s.isActive).length;

  return (
    <div className="uts-wrapper">
      {/* Background Grid */}
      <div className="uts-bg-grid" />

      {/* STAGE 1 & 2: Telemetry & Extraction */}
      <div className="uts-stage uts-telemetry-stage">
        <div className="uts-streams-container">
          {streams.map((stream, idx) => (
            <div key={stream.id} className="uts-stream-row">
              <div className="uts-stream-source">
                <span className="uts-ip">{stream.ip}</span>
              </div>
              <div className="uts-stream-track">
                {/* Continuous flowing particles */}
                <div className="uts-particle uts-p1" />
                <div className="uts-particle uts-p2" />
                <div className="uts-particle uts-p3" />
                
                {/* Signal tag that fades in */}
                <div className={`uts-signal-tag ${stream.isActive ? 'active' : ''}`} style={{ '--sig-color': stream.color } as React.CSSProperties}>
                  <div className="uts-signal-dot" style={{ backgroundColor: stream.color }} />
                  <span className="uts-signal-label">{stream.signal}</span>
                  
                  {/* Hover tooltip */}
                  <div className="uts-signal-tooltip">
                    <div className="uts-tt-title" style={{ color: stream.color }}>{stream.signal}</div>
                    <div className="uts-tt-desc">{stream.desc}</div>
                    <div className="uts-tt-obs">Observed: <span>{stream.observed}</span></div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Desktop Convergence SVG */}
      <div className="uts-convergence uts-hide-mobile">
        <svg viewBox="0 0 60 160" preserveAspectRatio="none" className="uts-conv-svg">
          {streams.map((stream, i) => {
            const startY = 20 + i * 40;
            const endY = 40 + i * 26;
            return (
              <path
                key={i}
                d={`M 0 ${startY} C 30 ${startY}, 30 ${endY}, 60 ${endY}`}
                className={`uts-conv-path ${stream.isActive ? 'active' : ''}`}
                style={{ stroke: stream.isActive ? stream.color : undefined }}
              />
            );
          })}
        </svg>
      </div>

      {/* Vertical Mobile Convergence (Arrows) */}
      <div className="uts-mobile-flow uts-show-mobile">
        <div className="uts-down-arrow" />
      </div>

      {/* STAGE 3: Evidence Correlation */}
      <div className="uts-stage uts-engine-stage">
        <div className={`uts-engine-module ${engineState}`}>
          <div className="uts-engine-header">
            <span className="uts-engine-title">EVIDENCE ENGINE</span>
            <div className={`uts-engine-indicator ${engineState === 'correlated' ? 'pulse' : ''}`} />
          </div>
          
          <div className="uts-engine-signals">
            {streams.map((stream, i) => (
              <div key={stream.id} className={`uts-engine-sig-row ${stream.isActive ? 'active' : ''}`}>
                <span className="uts-esig-name">{stream.signal.toLowerCase()}</span>
                <span className="uts-esig-dot" style={{ backgroundColor: stream.isActive ? stream.color : 'var(--uts-border)' }} />
              </div>
            ))}
          </div>

          <div className="uts-engine-footer">
            <span className={`uts-engine-status ${engineState === 'correlated' ? 'correlated' : ''}`}>
              {engineState === 'correlated' ? `${activeCount} SIGNALS CORRELATED` : 'AWAITING SIGNALS'}
            </span>
          </div>
        </div>
      </div>

      {/* Desktop Connection to Card */}
      <div className="uts-convergence uts-hide-mobile">
        <svg viewBox="0 0 40 160" preserveAspectRatio="none" className="uts-conv-svg">
          <path d="M 0 80 L 40 80" className={`uts-conv-path ${engineState === 'correlated' ? 'active-solid' : ''}`} />
          {engineState === 'correlated' && (
            <circle r="2" fill="var(--uts-cyan)" className="uts-alert-particle">
              <animateMotion dur="1s" repeatCount="indefinite" path="M 0 80 L 40 80" />
            </circle>
          )}
        </svg>
      </div>

      {/* Vertical Mobile Flow */}
      <div className="uts-mobile-flow uts-show-mobile">
        <div className="uts-down-arrow" />
      </div>

      {/* STAGE 4: Threat Detection */}
      <div className="uts-stage uts-detection-stage">
        <div className={`uts-threat-card ${engineState === 'correlated' ? 'detected' : ''}`}>
          <div className="uts-tc-header">
            <span className="uts-tc-label">THREAT DETECTED</span>
            <span className="uts-tc-pulse" />
          </div>
          
          <h4 className="uts-tc-threat-name">DNS TUNNELING</h4>
          
          <div className="uts-tc-metrics">
            <div className="uts-tc-metric">
              <span className="uts-tcm-label">RISK</span>
              <span className="uts-tcm-value uts-tcm-score">92 <span className="uts-tcm-sub">/ 100</span></span>
            </div>
            <div className="uts-tc-metric">
              <span className="uts-tcm-label">CONFIDENCE</span>
              <span className="uts-tcm-value">97%</span>
            </div>
          </div>
          
          <div className="uts-tc-summary">
            {activeCount} signals correlated<br/>
            12 supporting observations
          </div>
          
          <div className="uts-tc-action-wrap">
            <button className="uts-tc-action">
              VIEW EVIDENCE &rarr;
            </button>
          </div>
        </div>
      </div>

    </div>
  );
}
