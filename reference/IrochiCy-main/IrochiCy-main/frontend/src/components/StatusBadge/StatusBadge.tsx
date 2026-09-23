import type { AlertStatus } from '@/types';
import './StatusBadge.css';

const STATUS_LABELS: Record<AlertStatus, string> = {
  new: 'NEW',
  acknowledged: 'ACK',
  investigating: 'INVESTIGATING',
  closed: 'CLOSED',
  escalated: 'ESCALATED',
};

interface StatusBadgeProps {
  status: AlertStatus;
  large?: boolean;
}

export default function StatusBadge({ status, large }: StatusBadgeProps) {
  return (
    <span className={`status-badge status-badge--${status} ${large ? 'status-badge--large' : ''}`}>
      {STATUS_LABELS[status]}
    </span>
  );
}
