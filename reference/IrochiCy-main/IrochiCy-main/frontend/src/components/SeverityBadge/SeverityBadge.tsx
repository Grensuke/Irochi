import type { Severity } from '@/types';
import './SeverityBadge.css';

const SEVERITY_COLORS: Record<Severity, string> = {
  critical: 'var(--severity-critical)',
  high: 'var(--severity-high)',
  medium: 'var(--severity-medium)',
  low: 'var(--severity-low)',
  info: 'var(--severity-info)',
};

interface SeverityBadgeProps {
  severity: Severity;
  large?: boolean;
}

export default function SeverityBadge({ severity, large }: SeverityBadgeProps) {
  const color = SEVERITY_COLORS[severity];
  const shouldPulse = severity === 'critical' || severity === 'high';

  return (
    <span className={`severity-badge ${large ? 'severity-badge--large' : ''}`} style={{ color }}>
      <span
        className={`severity-badge__dot ${shouldPulse ? 'severity-badge__dot--pulse' : ''}`}
        style={{ backgroundColor: color }}
      />
      {severity.toUpperCase()}
    </span>
  );
}
