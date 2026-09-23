import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import type { ThreatType, Alert, DetectorSignal, ConfidenceBucket } from '@/types';
import { THREAT_FULL_NAMES } from '@/types';
import SignalBreakdown from '@/components/SignalBreakdown/SignalBreakdown';
import ConfidenceHistogram from '@/components/ConfidenceHistogram/ConfidenceHistogram';
import ConfidenceBar from '@/components/ConfidenceBar/ConfidenceBar';
import StatusBadge from '@/components/StatusBadge/StatusBadge';
import './ThreatDetail.css';

const THREAT_COLORS: Record<ThreatType, string> = {
  ddos: '#FF3B5C', recon: '#FF7A2F', dns: '#A78BFA', tls: '#5B8CFF', exfil: '#F5C518',
};

const DESCRIPTIONS: Record<ThreatType, string> = {
  ddos: 'Monitors connection telemetry for volumetric attack patterns. Derives packet_rate, byte_rate, syn_ratio, and source_ip_entropy over rolling windows. Triggers on rate thresholds and entropy spikes indicating distributed source traffic.',
  recon: 'Tracks port scanning and host discovery behavior by windowing unique destination ports and hosts per source IP. Detects horizontal and vertical scans. Uses statistical thresholds on connection_fan_out and scan_rate.',
  dns: 'Analyzes DNS query telemetry from Zeek dns.log for algorithmically generated domain names (DGA) and DNS tunneling. Scores queries by domain_entropy, n_gram likelihood, label-length statistics, and query_frequency. XGBoost classifier trained on labeled DGA corpora.',
  tls: 'Inspects TLS session fingerprints (JA3 from Zeek ssl.log) against the Abuse.ch SSLBL blacklist. Separately monitors connection timing for beacon periodicity. JA3 blacklist match is treated as medium-confidence; combined with timing regularity for high-confidence C2 classification.',
  exfil: 'Detects sustained large outbound data transfers by windowing outbound_inbound_ratio and rolling transfer volume. Flags sessions with byte asymmetry exceeding thresholds over configurable windows.',
};

const SIGNALS: Record<ThreatType, DetectorSignal[]> = {
  ddos: [
    { name: 'packet_rate', signalType: 'raw', threshold: '> 50k pps', weight: 0.9, triggeredToday: 45 },
    { name: 'byte_rate', signalType: 'raw', threshold: '> 100 MB/s', weight: 0.7, triggeredToday: 32 },
    { name: 'syn_ratio', signalType: 'derived', threshold: '> 0.8', weight: 0.85, triggeredToday: 28 },
    { name: 'src_ip_entropy', signalType: 'derived', threshold: '> 5.0', weight: 0.6, triggeredToday: 19 },
  ],
  recon: [
    { name: 'unique_dst_ports', signalType: 'derived', threshold: '> 100/min', weight: 0.8, triggeredToday: 34 },
    { name: 'unique_dst_hosts', signalType: 'derived', threshold: '> 50/min', weight: 0.75, triggeredToday: 22 },
    { name: 'connection_fan_out', signalType: 'derived', threshold: '> 200', weight: 0.7, triggeredToday: 18 },
    { name: 'scan_rate', signalType: 'raw', threshold: '> 1k/s', weight: 0.65, triggeredToday: 15 },
  ],
  dns: [
    { name: 'domain_entropy', signalType: 'derived', threshold: '> 3.5', weight: 0.9, triggeredToday: 41 },
    { name: 'n_gram_score', signalType: 'derived', threshold: '< 0.3', weight: 0.85, triggeredToday: 38 },
    { name: 'label_length', signalType: 'raw', threshold: '> 15 chars', weight: 0.5, triggeredToday: 29 },
    { name: 'query_frequency', signalType: 'raw', threshold: '> 50/min', weight: 0.6, triggeredToday: 24 },
    { name: 'xgb_dga_score', signalType: 'derived', threshold: '> 0.7', weight: 0.95, triggeredToday: 36 },
  ],
  tls: [
    { name: 'ja3_blacklist', signalType: 'intel', threshold: 'match', weight: 0.9, triggeredToday: 12 },
    { name: 'beacon_periodicity', signalType: 'derived', threshold: '< 0.1 jitter', weight: 0.85, triggeredToday: 8 },
    { name: 'cert_validity_days', signalType: 'raw', threshold: '< 30 days', weight: 0.4, triggeredToday: 15 },
    { name: 'sni_mismatch', signalType: 'derived', threshold: 'true', weight: 0.6, triggeredToday: 6 },
  ],
  exfil: [
    { name: 'outbound_ratio', signalType: 'derived', threshold: '> 10:1', weight: 0.85, triggeredToday: 11 },
    { name: 'rolling_volume', signalType: 'raw', threshold: '> 500 MB/hr', weight: 0.8, triggeredToday: 7 },
    { name: 'session_duration', signalType: 'raw', threshold: '> 3600s', weight: 0.5, triggeredToday: 14 },
    { name: 'byte_asymmetry', signalType: 'derived', threshold: '> 0.9', weight: 0.75, triggeredToday: 9 },
  ],
};

function relativeTime(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

interface ThreatDetailProps { type: ThreatType; count: number; recentAlerts: Alert[]; }

export default function ThreatDetail({ type, count, recentAlerts }: ThreatDetailProps) {
  const navigate = useNavigate();
  const color = THREAT_COLORS[type];
  const signals = SIGNALS[type];

  const buckets: ConfidenceBucket[] = useMemo(() =>
    Array.from({ length: 10 }, (_, i) => ({
      range: `${i * 10}-${(i + 1) * 10}%`,
      count: Math.round(Math.random() * (i < 3 ? 5 : i > 7 ? 30 : 15) + 2),
    })),
  [type]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="threat-detail">
      {/* Header */}
      <div className="threat-detail__header">
        <div>
          <div className="threat-detail__title">{THREAT_FULL_NAMES[type]}</div>
          <div className="threat-detail__status">
            <span className="threat-detail__status-dot" style={{ backgroundColor: 'var(--severity-low)' }} />
            <span style={{ color: 'var(--severity-low)' }}>ACTIVE — RUNNING</span>
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div className="threat-detail__big-num" style={{ color }}>{count}</div>
          <div className="threat-detail__big-sub">alerts generated in the last 24 hours</div>
        </div>
      </div>

      {/* Section 1: Overview */}
      <div className="threat-detail__section">
        <div className="threat-detail__section-title">DETECTOR OVERVIEW</div>
        <div className="threat-detail__desc">{DESCRIPTIONS[type]}</div>
      </div>

      {/* Section 2: Signal Breakdown */}
      <div className="threat-detail__section">
        <div className="threat-detail__section-title">DETECTION SIGNALS</div>
        <SignalBreakdown signals={signals} color={color} />
      </div>

      {/* Section 3: Confidence Histogram */}
      <div className="threat-detail__section">
        <div className="threat-detail__section-title">CONFIDENCE HISTOGRAM — TODAY</div>
        <ConfidenceHistogram buckets={buckets} color={color} />
      </div>

      {/* Section 4: Recent Detections */}
      <div className="threat-detail__section">
        <div className="threat-detail__section-title">RECENT DETECTIONS</div>
        <table className="threat-detail__recent-table">
          <thead>
            <tr><th>TIME</th><th>SRC IP</th><th>DST IP</th><th>CONFIDENCE</th><th>STATUS</th><th></th></tr>
          </thead>
          <tbody>
            {recentAlerts.slice(0, 10).map(a => (
              <tr key={a.alert_id}>
                <td>{relativeTime(a.created_at)}</td>
                <td>{a.src_ip}</td>
                <td>{a.dst_ip}</td>
                <td><ConfidenceBar value={a.confidence} /></td>
                <td><StatusBadge status={a.status} /></td>
                <td><span className="threat-detail__recent-link" onClick={() => navigate(`/alerts/${a.alert_id}`)}>→</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
