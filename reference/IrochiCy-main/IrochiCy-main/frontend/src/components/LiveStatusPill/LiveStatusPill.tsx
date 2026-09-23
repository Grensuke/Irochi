import type { WebSocketStatus } from '@/types';
import './LiveStatusPill.css';

interface LiveStatusPillProps {
  status: WebSocketStatus;
}

const STATUS_LABELS: Record<WebSocketStatus, string> = {
  connecting: 'CONNECTING',
  live: 'LIVE',
  reconnecting: 'RECONNECTING...',
  offline: 'OFFLINE',
};

export default function LiveStatusPill({ status }: LiveStatusPillProps) {
  return (
    <span className={`live-status-pill live-status-pill--${status}`}>
      <span className="live-status-pill__dot" />
      {STATUS_LABELS[status]}
    </span>
  );
}
