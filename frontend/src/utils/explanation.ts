import type { Alert } from '../types';
import { THREAT_TYPE_LABELS } from '../types';

const SIGNAL_NAMES: Record<string, string> = {
  outbound_inbound_ratio: 'outbound-to-inbound transfer ratio',
  byte_rate: 'byte transfer rate',
  connection_frequency: 'connection frequency',
  timing_regularity: 'timing regularity',
  jitter: 'timing jitter',
  ja3_blacklist_match: 'JA3 fingerprint blacklist match',
  packet_rate: 'packet rate',
  syn_ratio: 'SYN packet ratio',
  source_ip_entropy: 'source IP entropy',
  unique_destination_ports: 'unique destination ports count',
  connection_fan_out: 'connection fan-out ratio',
  unique_destination_hosts: 'unique destination hosts count',
  scan_rate: 'port scan rate'
};

function formatSignalNames(names: string[]): string {
  if (names.length === 0) return '';
  if (names.length === 1) return names[0];
  if (names.length === 2) return `${names[0]} and ${names[1]}`;
  const last = names.pop();
  return `${names.join(', ')}, and ${last}`;
}

export function generateExplanation(alert: Alert): string {
  const threatLabel = THREAT_TYPE_LABELS[alert.threat_type] || 'malicious';
  const evidence = alert.evidence;

  if (!evidence) {
    return alert.evidence_summary || `Potential ${threatLabel} activity was detected.`;
  }

  // Handle DGA (ML-based)
  if (alert.threat_type === 'dga_dns_tunnel' || evidence.probability !== undefined) {
    const prob = ((evidence.probability as number) * 100).toFixed(1);
    const thresh = ((evidence.threshold as number) * 100).toFixed(1);
    return `Suspicious DNS behavior was detected because the domain characteristics (such as entropy, length, and character ratios) resulted in a threat probability of ${prob}%, exceeding the model's threshold of ${thresh}%.`;
  }

  // Handle C2 Beaconing specifically to ensure correct signal directions
  if (alert.threat_type === 'c2_beaconing' && evidence.signals && Array.isArray(evidence.signals)) {
    const regularityTriggered = evidence.signals.find((s: any) => s.signal_name === 'timing_regularity' && s.triggered);
    const jitterTriggered = evidence.signals.find((s: any) => s.signal_name === 'jitter' && s.triggered);
    const notTriggeredNames = evidence.signals
      .filter((s: any) => !s.triggered)
      .map((s: any) => SIGNAL_NAMES[s.signal_name] || s.signal_name.replace(/_/g, ' '));
    
    const triggeredReasons = [];
    if (regularityTriggered) triggeredReasons.push('timing regularity met the detection threshold');
    if (jitterTriggered) triggeredReasons.push('timing jitter remained below its threshold');
    
    // Fallback if triggered signals exist but aren't strictly regularity/jitter (e.g. connection_frequency)
    evidence.signals.forEach((s: any) => {
      if (s.triggered && s.signal_name !== 'timing_regularity' && s.signal_name !== 'jitter') {
         triggeredReasons.push(`${SIGNAL_NAMES[s.signal_name] || s.signal_name.replace(/_/g, ' ')} exceeded its threshold`);
      }
    });

    let explanation = `Potential C2 beaconing behavior was detected because ${formatSignalNames(triggeredReasons)}.`;
    
    if (notTriggeredNames.length > 0) {
      explanation += ` ${formatSignalNames(notTriggeredNames)} did not independently trigger.`;
      explanation = explanation.replace(/\. ([a-z])/g, (_match, p1) => `. ${p1.toUpperCase()}`);
    }

    return explanation;
  }

  // Handle Multi-Signal (Heuristics)
  if (evidence.signals && Array.isArray(evidence.signals)) {
    const triggered = evidence.signals.filter((s: any) => s.triggered).map((s: any) => SIGNAL_NAMES[s.signal_name] || s.signal_name.replace(/_/g, ' '));
    const notTriggered = evidence.signals.filter((s: any) => !s.triggered).map((s: any) => SIGNAL_NAMES[s.signal_name] || s.signal_name.replace(/_/g, ' '));

    let explanation = `Potential ${threatLabel} behavior was detected because the observed ${formatSignalNames(triggered)} exceeded configured thresholds.`;

    if (notTriggered.length > 0) {
      explanation += ` Observed ${formatSignalNames(notTriggered)} contributed to the context but remained within normal limits.`;
    }

    return explanation;
  }

  return alert.evidence_summary || `Potential ${threatLabel} activity was detected based on observed traffic patterns.`;
}
