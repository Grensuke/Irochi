import type { ConnectionState } from '../types';
import './Header.css';

interface HeaderProps {
  connectionState: ConnectionState;
}

const STATE_LABELS: Record<ConnectionState, string> = {
  connecting: 'Connecting…',
  connected: 'Connected',
  backfilling: 'Backfilling…',
  live: 'Live',
  reconnecting: 'Reconnecting…',
  disconnected: 'Disconnected',
};

export function Header({ connectionState }: HeaderProps) {
  return (
    <header className="app-header">
      <div className="header-left">
        <div className="header-logo">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="10" r="8" stroke="var(--accent-primary)" strokeWidth="1.5" fill="none" />
            <circle cx="10" cy="10" r="3" fill="var(--accent-primary)" />
            <line x1="10" y1="2" x2="10" y2="6" stroke="var(--accent-primary)" strokeWidth="1.5" />
            <line x1="10" y1="14" x2="10" y2="18" stroke="var(--accent-primary)" strokeWidth="1.5" />
            <line x1="2" y1="10" x2="6" y2="10" stroke="var(--accent-primary)" strokeWidth="1.5" />
            <line x1="14" y1="10" x2="18" y2="10" stroke="var(--accent-primary)" strokeWidth="1.5" />
          </svg>
          <span className="header-title">IROCHI</span>
          <span className="header-subtitle">THREAT INTELLIGENCE</span>
        </div>
      </div>
      <div className="header-right">
        <div className="connection-indicator">
          <span className={`connection-dot ${connectionState}`} />
          <span className="connection-label">{STATE_LABELS[connectionState]}</span>
        </div>
      </div>
    </header>
  );
}
