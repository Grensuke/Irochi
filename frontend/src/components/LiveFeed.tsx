import { useState } from 'react';
import type { Alert, ConnectionState } from '../types';
import { formatTimestamp, threatLabel, formatConfidence, confidenceColor } from '../utils/format';
import { AlertDetail } from './AlertDetail';
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
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);

  return (
    <>
      <div className="panel live-feed-panel">
        <div className="panel-header">
          <span className="panel-title">Live Alert Feed</span>
          <div className="connection-indicator">
            <span className={`connection-dot ${connectionState}`} />
            <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
              {connectionState === 'live' ? 'Streaming' : connectionState}
            </span>
          </div>
        </div>
        <div className="live-feed-body">
          {connectionState === 'disconnected' && liveAlerts.length === 0 && (
            <div className="state-message">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M1 1l22 22M16.72 11.06A10.94 10.94 0 0 1 19 12.55" />
                <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39" />
                <path d="M10.71 5.05A16 16 0 0 1 22.56 9" />
                <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88" />
                <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
                <line x1="12" y1="20" x2="12.01" y2="20" />
              </svg>
              <span className="state-title">Not Connected</span>
              <span className="state-detail">WebSocket connection is not active.</span>
            </div>
          )}

          {(connectionState === 'connecting' || connectionState === 'reconnecting') && liveAlerts.length === 0 && (
            <div className="state-message">
              <div className="connecting-spinner" />
              <span className="state-title">
                {connectionState === 'connecting' ? 'Connecting…' : 'Reconnecting…'}
              </span>
            </div>
          )}

          {liveAlerts.map((entry, i) => (
            <div
              key={`${entry.alert.alert_id}-${entry.receivedAt}`}
              className={`live-alert-row ${i === 0 && entry.phase === 'live' ? 'animate-slide-in' : 'animate-fade-in'}`}
              onClick={() => setSelectedAlert(entry.alert)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && setSelectedAlert(entry.alert)}
            >
              <div className="live-alert-top">
                <span className={`severity-badge ${entry.alert.severity}`}>{entry.alert.severity}</span>
                <span className={`phase-badge ${entry.phase}`}>{entry.phase}</span>
                <span className="mono live-alert-time">{formatTimestamp(entry.alert.timestamp)}</span>
              </div>
              <div className="live-alert-body">
                <span className="live-alert-threat">{threatLabel(entry.alert.threat_type)}</span>
                <span className="live-alert-id mono">{entry.alert.alert_id}</span>
              </div>
              <div className="live-alert-meta">
                <span className="mono live-alert-ip">
                  {entry.alert.src_ip ?? '—'} → {entry.alert.dst_ip ?? '—'}
                </span>
                <span className="mono" style={{ color: confidenceColor(entry.alert.confidence) }}>
                  {formatConfidence(entry.alert.confidence)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {selectedAlert && (
        <AlertDetail alert={selectedAlert} onClose={() => setSelectedAlert(null)} />
      )}
    </>
  );
}
