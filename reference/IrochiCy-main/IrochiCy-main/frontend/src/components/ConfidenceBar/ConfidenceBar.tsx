import './ConfidenceBar.css';

interface ConfidenceBarProps {
  value: number; // 0.0 – 1.0
  large?: boolean;
}

function getColor(v: number): string {
  if (v >= 0.9) return 'var(--severity-critical)';
  if (v >= 0.7) return 'var(--severity-high)';
  if (v >= 0.4) return 'var(--severity-medium)';
  return 'var(--severity-low)';
}

export default function ConfidenceBar({ value, large }: ConfidenceBarProps) {
  const pct = Math.round(value * 100);
  const color = getColor(value);

  return (
    <div className={`confidence-bar ${large ? 'confidence-bar--large' : ''}`}>
      <span className="confidence-bar__value" style={{ color }}>{pct}%</span>
      <div className="confidence-bar__track">
        <div
          className="confidence-bar__fill"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}
