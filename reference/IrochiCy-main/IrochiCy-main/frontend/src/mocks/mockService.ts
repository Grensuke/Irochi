/* ═══════════════════════════════════════════════════════════════
   SIH-26145 Mock Data Service
   Generates realistic threat-detection data for development
   ═══════════════════════════════════════════════════════════════ */

import type {
  Alert,
  AlertStatus,
  ThreatType,
  Severity,
  Evidence,
  DashboardSummary,
  TimelineBucket,
  TopSourceIP,
  DetectorStatusInfo,
  ProtocolBreakdown,
  NetworkFlow,
  ConnStateCode,
  ConnStateInfo,
  CanonicalEvent,
} from '@/types';

// ─── Random Helpers ───
function randInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randFloat(min: number, max: number, decimals = 2): number {
  return parseFloat((Math.random() * (max - min) + min).toFixed(decimals));
}

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function uuid(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

// ─── Realistic IP pools ───
const INTERNAL_IPS = [
  '10.0.1.15', '10.0.1.22', '10.0.1.87', '10.0.2.4', '10.0.2.19',
  '10.0.3.101', '10.0.3.55', '172.16.0.12', '172.16.0.33', '172.16.1.8',
  '192.168.1.100', '192.168.1.205', '192.168.2.17', '192.168.10.5',
];

const EXTERNAL_IPS = [
  '45.33.32.156', '185.220.101.42', '91.219.236.135', '23.129.64.201',
  '104.244.72.115', '162.247.74.27', '198.96.155.3', '77.81.247.72',
  '209.141.33.61', '194.26.192.64', '103.25.61.114', '45.154.255.147',
  '89.248.167.131', '162.142.125.217', '71.6.199.11', '167.94.138.60',
];

const THREAT_TYPES: ThreatType[] = ['ddos', 'recon', 'dns', 'tls', 'exfil'];
const SEVERITIES: Severity[] = ['critical', 'high', 'medium', 'low', 'info'];
const PROTOCOLS: ('TCP' | 'UDP' | 'ICMP' | 'OTHER')[] = ['TCP', 'UDP', 'ICMP', 'OTHER'];

const COUNTRIES = [
  { name: 'Russia', code: 'RU' },
  { name: 'China', code: 'CN' },
  { name: 'United States', code: 'US' },
  { name: 'Netherlands', code: 'NL' },
  { name: 'Germany', code: 'DE' },
  { name: 'Romania', code: 'RO' },
  { name: 'Iran', code: 'IR' },
  { name: 'Brazil', code: 'BR' },
  { name: 'India', code: 'IN' },
  { name: 'Vietnam', code: 'VN' },
];

// ─── Evidence generators per threat type ───
function generateEvidence(threatType: ThreatType): Evidence[] {
  switch (threatType) {
    case 'ddos':
      return [
        { type: 'metric', description: 'Packet rate', value: `${randInt(50000, 500000)} pps` },
        { type: 'metric', description: 'SYN ratio', value: `${randFloat(0.7, 0.99)}` },
        { type: 'metric', description: 'Source IP entropy', value: `${randFloat(2.5, 8.0)}` },
      ];
    case 'recon':
      return [
        { type: 'metric', description: 'Unique destination ports', value: randInt(100, 65535) },
        { type: 'metric', description: 'Scan rate', value: `${randInt(50, 2000)} ports/s` },
        { type: 'metric', description: 'Connection fan-out', value: randInt(20, 500) },
      ];
    case 'dns':
      return [
        { type: 'metric', description: 'Domain entropy', value: `${randFloat(3.5, 5.0)}` },
        { type: 'metric', description: 'N-gram score', value: `${randFloat(0.01, 0.15)}` },
        { type: 'sample', description: 'Suspicious domain', value: `${randomDGA()}.com` },
      ];
    case 'tls':
      return [
        { type: 'metric', description: 'JA3 hash', value: randomJA3() },
        { type: 'indicator', description: 'SSLBL match', value: 'true' },
        { type: 'metric', description: 'Beacon periodicity', value: `${randFloat(0.8, 0.99)}` },
      ];
    case 'exfil':
      return [
        { type: 'metric', description: 'Outbound/inbound ratio', value: `${randFloat(5.0, 50.0)}` },
        { type: 'metric', description: 'Byte rate', value: `${randInt(100, 5000)} KB/s` },
        { type: 'metric', description: 'Transfer window', value: `${randInt(30, 300)}s` },
      ];
  }
}

function randomDGA(): string {
  const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
  const len = randInt(8, 16);
  let result = '';
  for (let i = 0; i < len; i++) {
    result += chars[Math.floor(Math.random() * chars.length)];
  }
  return result;
}

function randomJA3(): string {
  const hex = '0123456789abcdef';
  let result = '';
  for (let i = 0; i < 32; i++) {
    result += hex[Math.floor(Math.random() * hex.length)];
  }
  return result;
}

const ALERT_STATUSES: AlertStatus[] = ['new', 'acknowledged', 'investigating', 'closed', 'escalated'];

const THREAT_NAMES: Record<ThreatType, string[]> = {
  ddos: ['SYN Flood Attack', 'UDP Amplification', 'HTTP Flood', 'DNS Reflection'],
  recon: ['Port Scan Detected', 'Host Sweep', 'Service Enumeration', 'Banner Grabbing'],
  dns: ['DGA Domain Detection', 'DNS Tunneling', 'Suspicious Query Pattern', 'Fast Flux Detection'],
  tls: ['C2 Beacon Detected', 'Blacklisted JA3', 'Suspicious Certificate', 'TLS Covert Channel'],
  exfil: ['Large Data Transfer', 'Slow Exfiltration', 'DNS Exfiltration', 'Encrypted Tunnel Exfil'],
};

const ANALYSTS = ['Sarah Chen', 'Alex Morgan', 'James Wilson', 'Maria Garcia', 'Unassigned'];

// ─── Alert Generator ───
export function generateMockAlert(overrides?: Partial<Alert>): Alert {
  const threatType = overrides?.threat_type || pick(THREAT_TYPES);
  const severity = overrides?.severity || weightedSeverity(threatType);
  const srcIp = pick(EXTERNAL_IPS);

  return {
    alert_id: uuid(),
    threat_type: threatType,
    severity,
    src_ip: srcIp,
    dst_ip: pick(INTERNAL_IPS),
    src_port: randInt(1024, 65535),
    dst_port: pick([22, 53, 80, 443, 445, 3389, 8080, 8443]),
    protocol: threatType === 'dns' ? 'UDP' : pick(['TCP', 'UDP'] as const),
    confidence: randFloat(0.5, 0.99),
    evidence: generateEvidence(threatType),
    status: 'new' as AlertStatus,
    created_at: new Date(Date.now() - randInt(0, 300000)).toISOString(),
    detector_id: `det_${threatType}_001`,
    flagged_src: Math.random() < 0.2,
    flagged_dst: false,
    threat_name: pick(THREAT_NAMES[threatType]),
    assigned_to: Math.random() < 0.6 ? pick(ANALYSTS) : undefined,
    canonical_event: generateCanonicalEvent(srcIp, threatType),
    ...overrides,
  };
}

function weightedSeverity(threatType: ThreatType): Severity {
  const r = Math.random();
  if (threatType === 'ddos' || threatType === 'exfil') {
    if (r < 0.3) return 'critical';
    if (r < 0.55) return 'high';
    if (r < 0.8) return 'medium';
    return 'low';
  }
  if (r < 0.1) return 'critical';
  if (r < 0.3) return 'high';
  if (r < 0.6) return 'medium';
  if (r < 0.85) return 'low';
  return 'info';
}

// ─── Dashboard Summary ───
export function generateMockDashboardSummary(): DashboardSummary {
  return {
    totalAlertsToday: randInt(120, 380),
    totalAlertsDelta: randInt(-15, 40),
    activeThreats: randInt(8, 35),
    activeThreatsDelta: randInt(-5, 12),
    eventsPerSec: randInt(1200, 8500),
    detectorsActive: 5,
    detectorStatuses: generateDetectorStatuses(),
    pipelineLatencyMs: randInt(45, 350),
  };
}

function generateDetectorStatuses(): DetectorStatusInfo[] {
  const detectors: { id: string; name: string; threatType: ThreatType }[] = [
    { id: 'det_ddos_001', name: 'DDoS', threatType: 'ddos' },
    { id: 'det_recon_001', name: 'Recon', threatType: 'recon' },
    { id: 'det_dns_001', name: 'DNS-DGA', threatType: 'dns' },
    { id: 'det_tls_001', name: 'TLS-C2', threatType: 'tls' },
    { id: 'det_exfil_001', name: 'Exfiltration', threatType: 'exfil' },
  ];

  return detectors.map(d => ({
    ...d,
    status: Math.random() > 0.1 ? 'running' : (Math.random() > 0.5 ? 'idle' : 'error') as 'running' | 'idle' | 'error',
    lastDetection: new Date(Date.now() - randInt(30000, 600000)).toISOString(),
    alertsToday: randInt(5, 80),
    confidence: randFloat(0.6, 0.95),
  }));
}

// ─── Timeline (24h × 5 threat types) ───
export function generateMockTimeline(): TimelineBucket[] {
  const buckets: TimelineBucket[] = [];
  const now = new Date();

  for (let i = 23; i >= 0; i--) {
    const hour = new Date(now);
    hour.setHours(now.getHours() - i, 0, 0, 0);

    // Simulate higher activity during business hours
    const hourOfDay = hour.getHours();
    const multiplier = (hourOfDay >= 9 && hourOfDay <= 17) ? 2.5
      : (hourOfDay >= 18 && hourOfDay <= 22) ? 1.5
      : 0.8;

    buckets.push({
      hour: `${String(hour.getHours()).padStart(2, '0')}:00`,
      ddos: Math.round(randInt(2, 15) * multiplier),
      recon: Math.round(randInt(3, 20) * multiplier),
      dns: Math.round(randInt(1, 12) * multiplier),
      tls: Math.round(randInt(1, 8) * multiplier),
      exfil: Math.round(randInt(0, 5) * multiplier),
    });
  }

  return buckets;
}

// ─── Top Source IPs ───
export function generateMockTopIPs(): TopSourceIP[] {
  const shuffled = [...EXTERNAL_IPS].sort(() => Math.random() - 0.5);
  return shuffled.slice(0, 10).map((ip, index) => {
    const country = pick(COUNTRIES);
    return {
      rank: index + 1,
      ip,
      eventCount: Math.round((10 - index) * randInt(80, 200) + randInt(0, 100)),
      country: country.name,
      countryCode: country.code,
    };
  }).sort((a, b) => b.eventCount - a.eventCount)
    .map((item, index) => ({ ...item, rank: index + 1 }));
}

// ─── Protocol Breakdown ───
export function generateMockProtocolBreakdown(): ProtocolBreakdown[] {
  const tcp = randInt(55, 70);
  const udp = randInt(15, 25);
  const icmp = randInt(3, 8);
  const other = 100 - tcp - udp - icmp;

  const total = randInt(50000, 200000);

  return [
    { protocol: 'TCP', count: Math.round(total * tcp / 100), percentage: tcp, color: 'var(--accent-primary)' },
    { protocol: 'UDP', count: Math.round(total * udp / 100), percentage: udp, color: 'var(--severity-high)' },
    { protocol: 'ICMP', count: Math.round(total * icmp / 100), percentage: icmp, color: 'var(--threat-dns)' },
    { protocol: 'Other', count: Math.round(total * other / 100), percentage: other, color: 'var(--text-tertiary)' },
  ];
}

// ─── Live Alert Simulator ───
export function simulateLiveAlerts(
  callback: (alert: Alert) => void,
  intervalRange: [number, number] = [1000, 5000]
): () => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  let running = true;

  function scheduleNext() {
    if (!running) return;
    const delay = randInt(intervalRange[0], intervalRange[1]);
    timeoutId = setTimeout(() => {
      if (!running) return;
      const alert = generateMockAlert({
        created_at: new Date().toISOString(),
        status: 'new' as AlertStatus,
      });
      callback(alert);
      scheduleNext();
    }, delay);
  }

  scheduleNext();

  // Return cleanup function
  return () => {
    running = false;
    if (timeoutId) clearTimeout(timeoutId);
  };
}

// ─── Generate initial batch of alerts ───
export function generateInitialAlerts(count: number = 20): Alert[] {
  return Array.from({ length: count }, (_, i) => 
    generateMockAlert({
      created_at: new Date(Date.now() - (count - i) * randInt(10000, 60000)).toISOString(),
    })
  ).sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
}

// ─── Generate paginated alert list ───
export function generateAlertList(count: number = 100): Alert[] {
  const statuses: AlertStatus[] = ['new', 'acknowledged', 'investigating', 'closed', 'escalated'];
  return Array.from({ length: count }, (_, i) => 
    generateMockAlert({
      created_at: new Date(Date.now() - i * randInt(30000, 300000)).toISOString(),
      status: i < 10 ? 'new' : pick(statuses),
    })
  ).sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
}

// ─── Canonical Event Generator ───
function generateCanonicalEvent(srcIp: string, threatType: ThreatType): CanonicalEvent {
  return {
    event_id: uuid(),
    event_type: threatType === 'dns' ? 'dns' : threatType === 'tls' ? 'tls' : 'connection',
    ingest_timestamp: Date.now() * 1000,
    sensor_source: pick(['zeek', 'netflow', 'ipfix'] as const),
    src_ip: srcIp,
    dst_ip: pick(INTERNAL_IPS),
    src_port: randInt(1024, 65535),
    dst_port: pick([22, 53, 80, 443, 445]),
    protocol: threatType === 'dns' ? 'UDP' : 'TCP',
    schema_version: '1.2.0',
  };
}

// ─── Related Alerts ───
export function generateRelatedAlerts(srcIp: string, excludeId: string): Alert[] {
  return Array.from({ length: randInt(2, 5) }, () =>
    generateMockAlert({
      src_ip: srcIp,
      created_at: new Date(Date.now() - randInt(60000, 7200000)).toISOString(),
    })
  ).filter(a => a.alert_id !== excludeId);
}

// ─── Network Flow Generator ───
export function generateNetworkFlow(): NetworkFlow {
  const connStates: ConnStateCode[] = ['SF', 'S0', 'REJ', 'RSTO', 'RSTOS0', 'SH', 'OTH', 'S1'];
  const eventTypes: (ThreatType | 'normal')[] = ['normal', 'normal', 'normal', 'normal', 'ddos', 'recon', 'dns', 'tls', 'exfil'];
  const eventType = pick(eventTypes);

  return {
    id: uuid(),
    src_ip: pick(EXTERNAL_IPS),
    src_port: randInt(1024, 65535),
    dst_ip: pick(INTERNAL_IPS),
    dst_port: pick([22, 53, 80, 443, 445, 3389, 8080, 8443]),
    protocol: pick(['TCP', 'UDP'] as const),
    bytes_sent: randInt(64, 1048576),
    bytes_recv: randInt(64, 524288),
    duration: randFloat(0.01, 300),
    conn_state: pick(connStates),
    event_type: eventType,
    timestamp: new Date().toISOString(),
    suspicious: eventType !== 'normal' && Math.random() < 0.4,
  };
}

export function generateNetworkFlows(count: number): NetworkFlow[] {
  return Array.from({ length: count }, () => generateNetworkFlow());
}

// ─── Connection State Summary ───
export function generateConnStateSummary(): ConnStateInfo[] {
  return [
    { code: 'SF', name: 'Normal Established', count: randInt(5000, 20000), color: 'var(--severity-low)' },
    { code: 'S0', name: 'No Response', count: randInt(200, 2000), color: 'var(--severity-medium)' },
    { code: 'REJ', name: 'Rejected', count: randInt(100, 1500), color: 'var(--severity-medium)' },
    { code: 'RSTO', name: 'RST from Orig', count: randInt(50, 800), color: 'var(--severity-high)' },
    { code: 'RSTOS0', name: 'RST Orig, No Resp', count: randInt(20, 400), color: 'var(--severity-high)' },
    { code: 'RSTRH', name: 'RST Resp, Half', count: randInt(10, 200), color: 'var(--severity-high)' },
    { code: 'SH', name: 'Orig Half-Open', count: randInt(30, 500), color: 'var(--severity-medium)' },
    { code: 'SHR', name: 'Resp Half-Open', count: randInt(20, 300), color: 'var(--severity-medium)' },
    { code: 'OTH', name: 'Other / Midstream', count: randInt(50, 600), color: 'var(--text-tertiary)' },
    { code: 'S1', name: 'Established, No Close', count: randInt(100, 1000), color: 'var(--severity-info)' },
    { code: 'S2', name: 'Established, Close Orig', count: randInt(50, 500), color: 'var(--severity-info)' },
    { code: 'S3', name: 'Established, Close Resp', count: randInt(50, 500), color: 'var(--severity-info)' },
  ];
}
