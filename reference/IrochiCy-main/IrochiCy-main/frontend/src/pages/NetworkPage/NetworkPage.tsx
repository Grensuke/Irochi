import { useState, useMemo } from 'react';
import { generateConnStateSummary } from '@/mocks/mockService';
import FlowVisualizer from '@/components/FlowVisualizer/FlowVisualizer';
import ConnStateGrid from '@/components/ConnStateGrid/ConnStateGrid';
import LiveFlowTable from '@/components/LiveFlowTable/LiveFlowTable';
import PageTransition from '@/components/PageTransition/PageTransition';
import './NetworkPage.css';

export default function NetworkPage() {
  const [paused, setPaused] = useState(false);
  const [speed, setSpeed] = useState(1);
  const connStates = useMemo(() => generateConnStateSummary(), []);

  return (
    <PageTransition>
      <div className="network-page">
        {/* Top row: Flow Visualizer + Conn State Grid */}
        <div className="network-page__top-row">
          <div className="network-page__viz-panel">
            <div className="network-page__viz-title">LIVE EVENT STREAM</div>
            <FlowVisualizer speed={speed} paused={paused} />
            <div className="network-page__viz-controls">
              <button
                className={`network-page__viz-btn ${paused ? '' : 'network-page__viz-btn--active'}`}
                onClick={() => setPaused(p => !p)}
              >
                {paused ? '▶ RESUME' : '⏸ PAUSE'}
              </button>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>SPEED:</span>
              <div className="network-page__speed-group">
                {[1, 2, 5].map(s => (
                  <button
                    key={s}
                    className={`network-page__viz-btn ${speed === s ? 'network-page__viz-btn--active' : ''}`}
                    onClick={() => setSpeed(s)}
                  >{s}×</button>
                ))}
              </div>
            </div>
          </div>
          <ConnStateGrid states={connStates} />
        </div>

        {/* Bottom row: Live Flow Table */}
        <LiveFlowTable />
      </div>
    </PageTransition>
  );
}
