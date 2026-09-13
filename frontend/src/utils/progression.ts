import type { CorrelatedEvent } from './correlation';

export interface AttackProgression {
  stages: { name: string; observed: boolean }[];
}

export function deriveAttackProgression(events: CorrelatedEvent[]): AttackProgression {
  const observedThreats = new Set(events.map(e => e.alert.threat_type));
  
  // Potential logical stages in this specific SIH problem statement context
  const hasRecon = observedThreats.has('recon_portscan');
  const hasDiscovery = observedThreats.has('dga_dns_tunnel');
  const hasC2 = observedThreats.has('c2_beaconing') || observedThreats.has('encrypted_malware');
  const hasExfil = observedThreats.has('data_exfiltration');
  const hasDDoS = observedThreats.has('volumetric_ddos'); // DDoS is often standalone, but track it

  // If we only have DDoS, progression might not make sense as a chain, but we return observed stages
  const stages = [];
  
  if (hasRecon || hasDiscovery || hasC2 || hasExfil) {
    stages.push({ name: 'Reconnaissance', observed: hasRecon });
    stages.push({ name: 'Discovery / DNS', observed: hasDiscovery });
    stages.push({ name: 'C2 Communication', observed: hasC2 });
    stages.push({ name: 'Exfiltration', observed: hasExfil });
  } else if (hasDDoS) {
    stages.push({ name: 'Volumetric Attack', observed: true });
  }

  // Filter out any completely unobserved chains if it doesn't make sense, but the requirement is:
  // "Only show a progression when the real alert data supports the stages. Otherwise show: 'Related activity observed'"
  // We will return the full stage array if at least *two* logical progression steps exist, 
  // or just let the UI handle the rendering logic based on how many are observed.

  return { stages };
}
