import type { ThreatType } from '@/types';
import './ThreatSelector.css';

const THREAT_COLORS: Record<ThreatType, string> = {
  ddos: '#FF3B5C', recon: '#FF7A2F', dns: '#A78BFA', tls: '#5B8CFF', exfil: '#F5C518',
};

const THREATS: { type: ThreatType; name: string; sub: string }[] = [
  { type: 'ddos', name: 'DDoS', sub: 'DDoS Detector v1.2' },
  { type: 'recon', name: 'Reconnaissance', sub: 'Recon Detector v1.0' },
  { type: 'dns', name: 'DNS-DGA', sub: 'DGA Classifier v2.1' },
  { type: 'tls', name: 'TLS-C2', sub: 'JA3 Beacon v1.4' },
  { type: 'exfil', name: 'Exfiltration', sub: 'Exfil Monitor v1.1' },
];

interface ThreatSelectorProps {
  selected: ThreatType;
  onSelect: (t: ThreatType) => void;
  counts: Record<ThreatType, number>;
}

export default function ThreatSelector({ selected, onSelect, counts }: ThreatSelectorProps) {
  return (
    <div className="threat-selector">
      <div className="threat-selector__title">THREAT TYPES</div>
      {THREATS.map(t => {
        const active = selected === t.type;
        const color = THREAT_COLORS[t.type];
        return (
          <div
            key={t.type}
            className={`threat-selector__item ${active ? 'threat-selector__item--active' : ''}`}
            style={active ? { background: `${color}14` } : undefined}
            onClick={() => onSelect(t.type)}
          >
            <div className="threat-selector__bar" style={{ backgroundColor: color, color }} />
            <div className="threat-selector__info">
              <div className="threat-selector__name">{t.name}</div>
              <div className="threat-selector__sub">{t.sub}</div>
            </div>
            <div className="threat-selector__count" style={{ color }}>{counts[t.type]}</div>
          </div>
        );
      })}
    </div>
  );
}
