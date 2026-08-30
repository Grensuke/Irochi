/**
 * Centralized mock data for pages without backend support.
 *
 * All values are DEMO/MOCK data for presentation purposes only.
 * They do NOT represent real detection performance, model accuracy,
 * throughput, detection rates, or production metrics.
 *
 * Network events use ONLY fields from the Canonical Event Schema
 * (docs/data/CANONICAL_EVENT_SCHEMA_FINAL.md). No derived fields.
 */

import type { NetworkEvent, MockUser, MockOrganization, Alert } from '../types';

export const MOCK_ALERTS: Alert[] = [
  {
    alert_id: 'ALT-004182',
    timestamp: new Date().toISOString(),
    threat_type: 'volumetric_ddos',
    severity: 'critical',
    confidence: 0.96,
    src_ip: '192.168.24.17',
    dst_ip: '10.42.8.21',
    dst_port: 443,
    proto: 'TCP',
    status: 'investigating',
    evidence_summary: 'Traffic characteristics strongly match the learned SYN flood profile.',
    detector_id: 'ddos_detector',
    related_events: ['EVT-00001']
  },
  {
    alert_id: 'ALT-004181',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    threat_type: 'recon_portscan',
    severity: 'high',
    confidence: 0.88,
    src_ip: '10.0.4.55',
    dst_ip: '10.42.8.0',
    proto: 'TCP',
    status: 'new',
    evidence_summary: 'Sequential horizontal port scan detected targeting internal subnet.',
    detector_id: 'recon_detector',
    related_events: []
  },
  {
    alert_id: 'ALT-004180',
    timestamp: new Date(Date.now() - 7200000).toISOString(),
    threat_type: 'c2_beaconing',
    severity: 'high',
    confidence: 0.92,
    src_ip: '10.0.5.20',
    dst_ip: '198.51.100.42',
    dst_port: 443,
    proto: 'TLS',
    status: 'closed',
    evidence_summary: 'Periodic TLS connections with strict jitter profile and suspicious SNI.',
    detector_id: 'tls_c2_detector',
    related_events: []
  },
  {
    alert_id: 'ALT-004179',
    timestamp: new Date(Date.now() - 14400000).toISOString(),
    threat_type: 'dga_dns_tunnel',
    severity: 'medium',
    confidence: 0.75,
    src_ip: '10.0.3.42',
    dst_ip: '8.8.8.8',
    dst_port: 53,
    proto: 'UDP',
    status: 'new',
    evidence_summary: 'High entropy DNS queries indicating possible DGA algorithm.',
    detector_id: 'dns_dga_tunnel_detector',
    related_events: []
  },
  {
    alert_id: 'ALT-004178',
    timestamp: new Date(Date.now() - 28800000).toISOString(),
    threat_type: 'data_exfiltration',
    severity: 'critical',
    confidence: 0.98,
    src_ip: '10.0.1.200',
    dst_ip: '203.0.113.88',
    dst_port: 443,
    proto: 'TCP',
    status: 'new',
    evidence_summary: 'Sustained outbound transfer of 4.2GB exceeding historical baseline by 400%.',
    detector_id: 'exfiltration_detector',
    related_events: []
  }
];

// ------------------------------------------------------------------
// Mock User / Organization (presentation only)
// ------------------------------------------------------------------

export const MOCK_USER: MockUser = {
  id: 'user-001',
  name: 'Alex Kumar',
  email: 'alex.kumar@acme-energy.com',
  role: 'Security Analyst',
  avatar_initials: 'AK',
};

export const MOCK_ORG: MockOrganization = {
  id: 'org-001',
  name: 'Acme Energy',
  plan: 'Enterprise',
};

// ------------------------------------------------------------------
// Mock Network Events (Canonical Event Schema fields only)
// ------------------------------------------------------------------

export const MOCK_NETWORK_EVENTS: NetworkEvent[] = [
  {
    event_id: 'EVT-00001',
    event_type: 'connection',
    connection_id: 'C-abc123',
    timestamp: '2026-08-27T19:53:11Z',
    sensor_source: 'zeek-sensor-01',
    src_ip: '198.51.100.0',
    dst_ip: '10.0.5.20',
    src_port: 44821,
    dst_port: 80,
    protocol: 'tcp',
    orig_bytes: 1240,
    resp_bytes: 52400,
    orig_pkts: 12,
    resp_pkts: 38,
    conn_state: 'SF',
  },
  {
    event_id: 'EVT-00002',
    event_type: 'dns',
    connection_id: 'C-def456',
    timestamp: '2026-08-27T19:52:44Z',
    sensor_source: 'zeek-sensor-01',
    src_ip: '10.0.3.42',
    dst_ip: '8.8.8.8',
    src_port: 51023,
    dst_port: 53,
    protocol: 'udp',
    orig_bytes: 64,
    resp_bytes: 128,
    orig_pkts: 1,
    resp_pkts: 1,
    conn_state: null,
  },
  {
    event_id: 'EVT-00003',
    event_type: 'tls',
    connection_id: 'C-ghi789',
    timestamp: '2026-08-27T19:51:30Z',
    sensor_source: 'zeek-sensor-02',
    src_ip: '10.0.2.15',
    dst_ip: '203.0.113.47',
    src_port: 49812,
    dst_port: 443,
    protocol: 'tcp',
    orig_bytes: 3200,
    resp_bytes: 48000,
    orig_pkts: 24,
    resp_pkts: 36,
    conn_state: 'SF',
  },
  {
    event_id: 'EVT-00004',
    event_type: 'connection',
    connection_id: 'C-jkl012',
    timestamp: '2026-08-27T19:50:15Z',
    sensor_source: 'netflow-router-01',
    src_ip: '10.0.1.200',
    dst_ip: '10.0.5.0',
    src_port: 38211,
    dst_port: 22,
    protocol: 'tcp',
    orig_bytes: 4800,
    resp_bytes: 2100,
    orig_pkts: 42,
    resp_pkts: 38,
    conn_state: 'SF',
  },
  {
    event_id: 'EVT-00005',
    event_type: 'dns',
    connection_id: 'C-mno345',
    timestamp: '2026-08-27T19:49:02Z',
    sensor_source: 'zeek-sensor-01',
    src_ip: '10.0.4.88',
    dst_ip: '192.0.2.199',
    src_port: 52100,
    dst_port: 53,
    protocol: 'udp',
    orig_bytes: 72,
    resp_bytes: 256,
    orig_pkts: 1,
    resp_pkts: 1,
    conn_state: null,
  },
  {
    event_id: 'EVT-00006',
    event_type: 'connection',
    connection_id: 'C-pqr678',
    timestamp: '2026-08-27T19:48:33Z',
    sensor_source: 'netflow-router-01',
    src_ip: '10.0.2.77',
    dst_ip: '198.51.100.55',
    src_port: 12345,
    dst_port: 443,
    protocol: 'tcp',
    orig_bytes: 89000,
    resp_bytes: 1200,
    orig_pkts: 620,
    resp_pkts: 18,
    conn_state: 'S1',
  },
  {
    event_id: 'EVT-00007',
    event_type: 'tls',
    connection_id: 'C-stu901',
    timestamp: '2026-08-27T19:47:10Z',
    sensor_source: 'zeek-sensor-02',
    src_ip: '10.0.4.55',
    dst_ip: '203.0.113.88',
    src_port: 50122,
    dst_port: 443,
    protocol: 'tcp',
    orig_bytes: 5600,
    resp_bytes: 112000,
    orig_pkts: 44,
    resp_pkts: 82,
    conn_state: 'SF',
  },
  {
    event_id: 'EVT-00008',
    event_type: 'connection',
    connection_id: 'C-vwx234',
    timestamp: '2026-08-27T19:46:05Z',
    sensor_source: 'zeek-sensor-01',
    src_ip: '192.0.2.0',
    dst_ip: '10.0.5.20',
    src_port: 33001,
    dst_port: 80,
    protocol: 'tcp',
    orig_bytes: 320,
    resp_bytes: 0,
    orig_pkts: 8,
    resp_pkts: 0,
    conn_state: 'REJ',
  },
];

// ------------------------------------------------------------------
// Mock Analytics Data
// DEMO/MOCK VALUES ONLY — not real metrics
// ------------------------------------------------------------------

export const MOCK_ALERT_TREND = [
  { label: 'Mon', value: 8 },
  { label: 'Tue', value: 14 },
  { label: 'Wed', value: 6 },
  { label: 'Thu', value: 22 },
  { label: 'Fri', value: 18 },
  { label: 'Sat', value: 4 },
  { label: 'Sun', value: 12 },
];

export const MOCK_SEVERITY_TREND = [
  { label: 'Mon', critical: 1, high: 3, medium: 3, low: 1 },
  { label: 'Tue', critical: 2, high: 5, medium: 4, low: 3 },
  { label: 'Wed', critical: 0, high: 2, medium: 3, low: 1 },
  { label: 'Thu', critical: 4, high: 8, medium: 6, low: 4 },
  { label: 'Fri', critical: 3, high: 6, medium: 5, low: 4 },
  { label: 'Sat', critical: 0, high: 1, medium: 2, low: 1 },
  { label: 'Sun', critical: 1, high: 4, medium: 4, low: 3 },
];

export const MOCK_CONFIDENCE_DIST = [
  { range: '90-100%', count: 4 },
  { range: '80-89%', count: 6 },
  { range: '70-79%', count: 8 },
  { range: '60-69%', count: 3 },
  { range: '50-59%', count: 2 },
  { range: '<50%', count: 1 },
];

// ------------------------------------------------------------------
// Mock Settings Data (presentation only — no real CRUD/auth/RBAC)
// ------------------------------------------------------------------

export const MOCK_TEAM_MEMBERS = [
  { id: 'user-001', name: 'Alex Kumar', email: 'alex.kumar@acme-energy.com', role: 'Security Analyst', status: 'active' },
  { id: 'user-002', name: 'Priya Sharma', email: 'priya.sharma@acme-energy.com', role: 'SOC Manager', status: 'active' },
  { id: 'user-003', name: 'Ravi Patel', email: 'ravi.patel@acme-energy.com', role: 'Network Engineer', status: 'active' },
  { id: 'user-004', name: 'Meera Joshi', email: 'meera.joshi@acme-energy.com', role: 'Security Analyst', status: 'inactive' },
];

export const MOCK_ROLES = [
  { name: 'SOC Manager', description: 'Full access to all features and configuration', users: 1 },
  { name: 'Security Analyst', description: 'View alerts, events, and analytics', users: 2 },
  { name: 'Network Engineer', description: 'View network events and basic analytics', users: 1 },
  { name: 'Read Only', description: 'View-only access to dashboards', users: 0 },
];

// ------------------------------------------------------------------
// Mock Ingest / System Status  (DEMO/MOCK — not real infrastructure state)
// ------------------------------------------------------------------

export const MOCK_INGEST_STATUS = {
  status: 'passive' as const,
  message: 'Observing passive telemetry',
  sensors: [
    { id: 'zeek-sensor-01', label: 'Zeek Sensor 01', connected: true },
    { id: 'zeek-sensor-02', label: 'Zeek Sensor 02', connected: true },
    { id: 'netflow-router-01', label: 'NetFlow Router 01', connected: true },
  ],
};

// ------------------------------------------------------------------
// Mock Traffic Timeseries  (DEMO/MOCK — not real throughput data)
// ------------------------------------------------------------------

export const MOCK_TRAFFIC_TIMESERIES = [
  { time: '00:00', bps: 42_000_000 },
  { time: '02:00', bps: 28_000_000 },
  { time: '04:00', bps: 15_000_000 },
  { time: '06:00', bps: 31_000_000 },
  { time: '08:00', bps: 88_000_000 },
  { time: '10:00', bps: 120_000_000 },
  { time: '12:00', bps: 105_000_000 },
  { time: '14:00', bps: 134_000_000 },
  { time: '16:00', bps: 118_000_000 },
  { time: '18:00', bps: 92_000_000 },
  { time: '20:00', bps: 76_000_000 },
  { time: '22:00', bps: 55_000_000 },
];

export const MOCK_PROTOCOL_DIST = [
  { protocol: 'TCP', pct: 61 },
  { protocol: 'UDP', pct: 22 },
  { protocol: 'TLS', pct: 12 },
  { protocol: 'ICMP', pct: 3 },
  { protocol: 'Other', pct: 2 },
];

// ------------------------------------------------------------------
// Mock Evidence by Alert  (DEMO/MOCK — not real forensic data)
// ------------------------------------------------------------------

export const MOCK_EVIDENCE_BY_ALERT: Record<string, string[]> = {
  'default': [
    'Observed traffic pattern matched known signature.',
    'Confidence threshold exceeded based on passive telemetry.',
    'No active remediation has been applied.',
  ],
};
