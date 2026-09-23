import type { DetectorSignal, SignalType } from '@/types';
import './SignalBreakdown.css';

interface SignalBreakdownProps { signals: DetectorSignal[]; color: string; }

function TypePill({ type }: { type: SignalType }) {
  return <span className={`signal-type-pill signal-type-pill--${type}`}>{type}</span>;
}

export default function SignalBreakdown({ signals, color }: SignalBreakdownProps) {
  return (
    <table className="signal-table">
      <thead>
        <tr>
          <th>SIGNAL NAME</th>
          <th>TYPE</th>
          <th>THRESHOLD</th>
          <th>WEIGHT</th>
          <th>TRIGGERED TODAY</th>
        </tr>
      </thead>
      <tbody>
        {signals.map((s, i) => (
          <tr key={i}>
            <td><span className="signal-name">{s.name}</span></td>
            <td><TypePill type={s.signalType} /></td>
            <td><span className="signal-threshold">{s.threshold}</span></td>
            <td>
              <div className="signal-weight-bar">
                <div className="signal-weight-fill" style={{ width: `${s.weight * 100}%`, backgroundColor: color }} />
              </div>
            </td>
            <td><span className="signal-triggered" style={{ color }}>{s.triggeredToday}</span></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
