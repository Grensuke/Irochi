import type { Evidence, ThreatType } from '@/types';
import './EvidenceTimeline.css';

const TYPE_COLORS: Record<string, string> = {
  metric: 'var(--severity-info)', indicator: 'var(--severity-critical)', sample: 'var(--severity-medium)',
};

interface EvidenceTimelineProps { evidence: Evidence[]; threatType: ThreatType; }

export default function EvidenceTimeline({ evidence }: EvidenceTimelineProps) {
  return (
    <div className="evidence-tl">
      <div className="evidence-tl__title">EVIDENCE CHAIN</div>
      <div className="evidence-tl__list">
        <div className="evidence-tl__line" />
        {evidence.map((ev, i) => {
          const color = TYPE_COLORS[ev.type] || 'var(--accent-primary)';
          return (
            <div key={i} className="evidence-tl__item">
              <div className="evidence-tl__dot" style={{ backgroundColor: color }} />
              <div className="evidence-tl__time">Evidence #{i + 1}</div>
              <div className="evidence-tl__type" style={{ color }}>{ev.description}</div>
              <div className="evidence-tl__value">{String(ev.value)}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
