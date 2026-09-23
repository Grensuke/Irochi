import type { ThreatType } from '@/types';
import './ThreatTypePill.css';

const THREAT_STYLES: Record<ThreatType, { bg: string; text: string }> = {
  ddos:  { bg: 'rgba(255,59,92,0.12)',   text: '#FF3B5C' },
  recon: { bg: 'rgba(255,122,47,0.12)',  text: '#FF7A2F' },
  dns:   { bg: 'rgba(167,139,250,0.12)', text: '#A78BFA' },
  tls:   { bg: 'rgba(91,140,255,0.12)',  text: '#5B8CFF' },
  exfil: { bg: 'rgba(245,197,24,0.12)',  text: '#F5C518' },
};

const THREAT_LABELS: Record<ThreatType, string> = {
  ddos: 'DDOS', recon: 'RECON', dns: 'DNS-DGA', tls: 'TLS-C2', exfil: 'EXFIL',
};

interface ThreatTypePillProps {
  type: ThreatType;
  large?: boolean;
}

export default function ThreatTypePill({ type, large }: ThreatTypePillProps) {
  const style = THREAT_STYLES[type];
  return (
    <span
      className={`threat-pill ${large ? 'threat-pill--large' : ''}`}
      style={{ backgroundColor: style.bg, color: style.text }}
    >
      {THREAT_LABELS[type]}
    </span>
  );
}
