import { useNavigate } from 'react-router-dom';
import type { Alert, ConnectionState } from '../types';
import { formatTimestamp, threatLabel, formatConfidence, confidenceColor } from '../utils/format';
import './LiveFeed.css';

interface LiveAlert {
  alert: Alert;
  phase: 'backfill' | 'live';
  receivedAt: number;
}

interface LiveFeedProps {
  liveAlerts: LiveAlert[];
  connectionState: ConnectionState;
}

export function LiveFeed({ liveAlerts, connectionState }: LiveFeedProps) {
  const navigate = useNavigate();

  return (
    <div className="panel live-feed-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: 'var(--space-3)' }}>
        <span className="panel-title">LIVE DETECTION STREAM</span>
        <div className="connection-indicator">
          <span className={`connection-dot ${connectionState}`} />
          <span style={{ color: 'var(--text-muted)', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {connectionState === 'live' ? 'Streaming' : connectionState}
          </span>
        </div>
      </div>
      <div className="live-feed-body" style={{ flex: 1, padding: 0 }}>
        {connectionState === 'disconnected' && liveAlerts.length === 0 && (
          <div className="state-message" style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '13px', fontWeight: 500, letterSpacing: '0.05em' }}>NOT CONNECTED</span>
            <span style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '6px' }}>WebSocket connection is offline.</span>
          </div>
        )}

        {(connectionState === 'connecting' || connectionState === 'reconnecting') && liveAlerts.length === 0 && (
          <div className="state-message" style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <div className="connecting-spinner" style={{ marginBottom: '12px' }} />
            <span style={{ color: 'var(--text-muted)', fontSize: '13px', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
              {connectionState}
            </span>
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {liveAlerts.map((entry, i) => (
            <div
              key={`${entry.alert.alert_id}-${entry.receivedAt}`}
              className={`live-alert-row ${i === 0 && entry.phase === 'live' ? 'animate-slide-in' : 'animate-fade-in'}`}
              style={{ 
                padding: 'var(--space-3) var(--space-4)', 
                borderBottom: '1px solid rgba(255, 255, 255, 0.03)',
                cursor: 'pointer',
                transition: 'background-color 0.2s ease',
              }}
              onClick={() => navigate(`/app/alerts/${entry.alert.alert_id}`)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && navigate(`/app/alerts/${entry.alert.alert_id}`)}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-panel-dark)'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span className={`severity-badge ${entry.alert.severity}`} style={{ padding: '2px 6px', fontSize: '9px', borderRadius: '2px' }}>
                    SEVERITY: {entry.alert.severity.toUpperCase()}
                  </span>
                  <span style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-primary)' }}>{threatLabel(entry.alert.threat_type)}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  {entry.phase === 'backfill' && (
                    <span style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>BACKFILL</span>
                  )}
                  <span className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{formatTimestamp(entry.alert.timestamp)}</span>
                </div>
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                  <div style={{ display: 'flex', gap: '6px', alignItems: 'baseline' }}>
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>SRC</span>
                    <span className="mono" style={{ fontSize: '11px', color: entry.alert.src_ip ? 'var(--text-secondary)' : 'var(--text-muted)' }}>{entry.alert.src_ip || '—'}</span>
                  </div>
                  <div style={{ display: 'flex', gap: '6px', alignItems: 'baseline' }}>
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>DST</span>
                    <span className="mono" style={{ fontSize: '11px', color: entry.alert.dst_ip ? 'var(--text-secondary)' : 'var(--text-muted)' }}>{entry.alert.dst_ip || '—'}</span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '6px', alignItems: 'baseline' }}>
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>CONF</span>
                  <span className="mono" style={{ fontSize: '11px', color: confidenceColor(entry.alert.confidence) }}>
                    {formatConfidence(entry.alert.confidence)}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
