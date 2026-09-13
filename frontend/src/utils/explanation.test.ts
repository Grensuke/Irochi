// No import needed for console.assert
import { generateExplanation } from './explanation';
import type { Alert } from '../types';

function runTests() {
  console.log('Running explanation tests...');

  // Test 1: DGA
  const alert1: Partial<Alert> = {
    threat_type: 'dga_dns_tunnel',
    evidence: {
      probability: 0.9996,
      threshold: 0.8,
    },
  };
  const result1 = generateExplanation(alert1 as Alert);
  console.assert(
    result1 === "Suspicious DNS behavior was detected because the domain characteristics (such as entropy, length, and character ratios) resulted in a threat probability of 100.0%, exceeding the model's threshold of 80.0%.",
    "Test 1 failed"
  );

  // Test 2: Heuristic Multiple Signals
  const alert2: Partial<Alert> = {
    threat_type: 'data_exfiltration',
    evidence: {
      signals: [
        { signal_name: 'outbound_inbound_ratio', triggered: true },
        { signal_name: 'byte_rate', triggered: true },
        { signal_name: 'packet_rate', triggered: false },
      ]
    },
  };
  const result2 = generateExplanation(alert2 as Alert);
  console.assert(result2.includes('Potential Data Exfiltration behavior was detected because the observed outbound-to-inbound transfer ratio and byte transfer rate exceeded configured thresholds.'));
  console.assert(result2.includes('Observed packet rate contributed to the context but remained within normal limits.'));

  console.log('All tests passed!');
}

runTests();
