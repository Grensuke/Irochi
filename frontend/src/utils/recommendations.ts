import type { Alert } from '../types';

export interface Recommendations {
  immediate: string[];
  preventive: string[];
}

export function generateRecommendations(alert: Alert): Recommendations {
  const immediate: string[] = [];
  const preventive: string[] = [];

  const evidence = alert.evidence;
  const triggeredSignals = new Set(
    (evidence?.signals || [])
      .filter((s: any) => s.triggered)
      .map((s: any) => s.signal_name)
  );

  switch (alert.threat_type) {
    case 'volumetric_ddos':
      if (triggeredSignals.has('packet_rate') && triggeredSignals.has('syn_ratio')) {
        immediate.push('Investigate the affected destination and review upstream rate-limiting or DDoS controls. Elevated packet rate and SYN packet ratio were observed.');
      } else {
        immediate.push('Investigate affected destination.');
        immediate.push('Check upstream/WAF/DDoS mitigation controls.');
      }
      immediate.push('Identify major traffic sources.');
      immediate.push('Apply temporary rate limiting where appropriate.');
      
      preventive.push('Enable/strengthen rate limiting.');
      preventive.push('Review exposed services.');
      preventive.push('Verify upstream DDoS mitigation.');
      break;

    case 'recon_portscan':
      if (triggeredSignals.has('unique_destination_ports')) {
        immediate.push('Investigate the source IP targeting an abnormally high number of unique destination ports.');
      } else {
        immediate.push('Investigate the source IP.');
        immediate.push('Review targeted destination ports.');
      }
      immediate.push('Determine whether the source is internal or external.');
      immediate.push('Review firewall/network logs.');
      immediate.push('Consider temporary blocking when justified.');

      preventive.push('Minimize exposed ports.');
      preventive.push('Strengthen firewall policy.');
      preventive.push('Improve network segmentation.');
      break;

    case 'dga_dns_tunnel':
      immediate.push('Investigate the originating endpoint.');
      immediate.push('Review the suspicious domain.');
      immediate.push('Check DNS request history.');
      immediate.push('Inspect associated processes/connections.');

      preventive.push('Improve DNS filtering.');
      preventive.push('Block known malicious/suspicious domains.');
      preventive.push('Monitor anomalous DNS patterns.');
      break;

    case 'c2_beaconing':
      if (triggeredSignals.has('timing_regularity')) {
        immediate.push('Investigate the affected endpoint. Highly regular timing behavior indicates potential automated beaconing.');
      } else {
        immediate.push('Investigate the affected endpoint.');
        immediate.push('Review repeated connection behavior.');
      }
      immediate.push('Inspect the recurring destination.');
      immediate.push('Inspect associated processes and outbound connections.');
      immediate.push('Consider endpoint isolation when severity warrants it.');

      preventive.push('Restrict unnecessary outbound traffic.');
      preventive.push('Improve DNS/domain filtering.');
      preventive.push('Maintain threat-intelligence feeds.');
      preventive.push('Monitor recurring outbound connections.');
      break;

    case 'data_exfiltration':
      if (triggeredSignals.has('outbound_inbound_ratio')) {
        immediate.push('Investigate the source endpoint and destination because outbound traffic was strongly dominant in the observed window.');
      } else {
        immediate.push('Investigate the source endpoint.');
        immediate.push('Review unusual outbound volume/rate.');
      }
      immediate.push('Identify the destination receiving outbound data.');
      immediate.push('Inspect recent files/processes or data-access activity.');
      immediate.push('Consider containment when severity warrants it.');

      preventive.push('Restrict outbound data flows.');
      preventive.push('Review egress controls.');
      preventive.push('Monitor abnormal transfer volumes.');
      preventive.push('Apply least-privilege access to sensitive data.');
      break;
      
    default:
      immediate.push('Investigate the involved entities based on observed activity.');
      immediate.push('Review relevant logs and context.');
      
      preventive.push('Review general security posture and controls for this environment.');
      break;
  }

  return { immediate, preventive };
}
