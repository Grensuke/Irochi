// No import needed for console.assert
import { generateRecommendations } from './recommendations';
import type { Alert } from '../types';

function runTests() {
  console.log('Running recommendation tests...');

  // 1. DDoS missing specific evidence
  const ddosAlert: Partial<Alert> = {
    threat_type: 'volumetric_ddos',
    evidence: { signals: [] }
  };
  const ddosRecs = generateRecommendations(ddosAlert as Alert);
  console.assert(ddosRecs.immediate.includes('Investigate affected destination.'));
  console.assert(ddosRecs.preventive.includes('Enable/strengthen rate limiting.'));

  // 2. DDoS with specific evidence
  const ddosEvidenceAlert: Partial<Alert> = {
    threat_type: 'volumetric_ddos',
    evidence: {
      signals: [
        { signal_name: 'packet_rate', triggered: true },
        { signal_name: 'syn_ratio', triggered: true }
      ]
    }
  };
  const ddosEvidenceRecs = generateRecommendations(ddosEvidenceAlert as Alert);
  console.assert(ddosEvidenceRecs.immediate.includes('Investigate the affected destination and review upstream rate-limiting or DDoS controls. Elevated packet rate and SYN packet ratio were observed.'));
  console.assert(!ddosEvidenceRecs.immediate.includes('Investigate affected destination.'));

  // 3. Exfiltration with specific evidence
  const exfilAlert: Partial<Alert> = {
    threat_type: 'data_exfiltration',
    evidence: {
      signals: [{ signal_name: 'outbound_inbound_ratio', triggered: true }]
    }
  };
  const exfilRecs = generateRecommendations(exfilAlert as Alert);
  console.assert(exfilRecs.immediate.includes('Investigate the source endpoint and destination because outbound traffic was strongly dominant in the observed window.'));

  // 4. Unknown threat type
  const unknownAlert: Partial<Alert> = {
    threat_type: 'unknown_type' as any,
    evidence: {}
  };
  const unknownRecs = generateRecommendations(unknownAlert as Alert);
  console.assert(unknownRecs.immediate.includes('Investigate the involved entities based on observed activity.'));

  console.log('All recommendation tests passed!');
}

runTests();
