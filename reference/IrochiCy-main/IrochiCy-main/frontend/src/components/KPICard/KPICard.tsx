import type { KPIData } from '@/types';
import './KPICard.css';

interface KPICardProps extends KPIData {
  suffix?: string;
  valueClassName?: string;
  detectorDots?: { color: string; active: boolean }[];
}

export default function KPICard({
  label,
  value,
  delta,
  deltaLabel,
  deltaDirection,
  borderColor,
  showPulse,
  suffix,
  valueClassName,
  detectorDots,
}: KPICardProps) {
  const formatValue = (v: number): string => {
    if (v >= 10000) return `${(v / 1000).toFixed(1)}k`;
    return v.toLocaleString();
  };

  const arrowChar = deltaDirection === 'up' ? '↑' : deltaDirection === 'down' ? '↓' : '→';

  return (
    <div
      className="kpi-card kpi-card--bordered"
      style={borderColor ? { borderLeftColor: borderColor } : undefined}
    >
      <div className="kpi-card__label">
        {label}
        {showPulse && <span className="kpi-card__pulse" />}
      </div>
      <div className={`kpi-card__value ${valueClassName || ''}`}>
        {formatValue(value)}
        {suffix && <span style={{ fontSize: 'var(--text-md)', marginLeft: '4px' }}>{suffix}</span>}
      </div>
      <div className="kpi-card__delta">
        <span className={`kpi-card__delta-arrow--${deltaDirection}`}>
          {arrowChar}
        </span>
        <span>{Math.abs(delta)} {deltaLabel}</span>
      </div>
      {detectorDots && (
        <div className="kpi-card__dots">
          {detectorDots.map((dot, i) => (
            <span
              key={i}
              className="kpi-card__dot"
              style={{
                backgroundColor: dot.active ? dot.color : 'var(--border-default)',
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
