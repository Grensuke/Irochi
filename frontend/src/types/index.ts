/**
 * Irochi frontend domain types.
 *
 * These types match the dummy backend API response structure
 * defined in docs/shared/API_CONTRACT.md.
 *
 * IMPORTANT: These are PRESENTATION types for the frontend.
 * They are NOT canonical event types. Do not conflate alert
 * presentation fields with the Canonical Event Schema.
 */

// ------------------------------------------------------------------
// Threat Taxonomy (Section 12 of init prompt)
// ------------------------------------------------------------------

/** Five logical detector modules (NOT microservices). */
export type DetectorId =
  | 'ddos_detector'
  | 'recon_detector'
  | 'dns_dga_tunnel_detector'
  | 'tls_c2_detector'
  | 'exfiltration_detector';

/** Six threat capabilities shown to users. */
export type ThreatType =
  | 'volumetric_ddos'
  | 'c2_beaconing'
  | 'dga_dns_tunnel'
  | 'encrypted_malware'
  | 'recon_portscan'
  | 'data_exfiltration';

/** Alert severity levels. */
export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';

/**
 * Alert lifecycle status — analyst workflow.
 * "Closed" does NOT imply Irochi mitigated the threat.
 * Irochi is a passive detection/intelligence system.
 */
export type AlertStatus = 'new' | 'investigating' | 'closed' | 'false_positive';

// ------------------------------------------------------------------
// Alert
// ------------------------------------------------------------------

export interface Alert {
  alert_id: string;
  timestamp: string;
  threat_type: ThreatType;
  detector_id: DetectorId;
  severity: Severity;
  confidence: number;
  src_ip: string | null;
  src_port: number | null;
  dst_ip: string | null;
  dst_port: number | null;
  evidence_summary: string;
  status: AlertStatus;
}

// ------------------------------------------------------------------
// API Responses
// ------------------------------------------------------------------

export interface AlertListResponse {
  alerts: Alert[];
  total: number;
}

export interface DashboardSummary {
  total_alerts: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  info_count: number;
  by_threat_type: Record<string, number>;
  by_detector: Record<string, number>;
  recent_alerts: Alert[];
}

export interface HealthResponse {
  status: string;
}

// ------------------------------------------------------------------
// WebSocket Messages
// ------------------------------------------------------------------

export type WsMessageType = 'backfill' | 'live' | 'backfill_complete';

export interface WsMessage {
  type: WsMessageType;
  alert: Alert | null;
}

// ------------------------------------------------------------------
// Connection State
// ------------------------------------------------------------------

export type ConnectionState =
  | 'connecting'
  | 'connected'
  | 'backfilling'
  | 'live'
  | 'reconnecting'
  | 'disconnected';

// ------------------------------------------------------------------
// Network Event (compatible with Canonical Event Schema)
// Fields from docs/data/CANONICAL_EVENT_SCHEMA_FINAL.md only.
// ------------------------------------------------------------------

export type EventType = 'connection' | 'dns' | 'tls';

export interface NetworkEvent {
  event_id: string;
  event_type: EventType;
  connection_id: string;
  timestamp: string;
  sensor_source: string;
  src_ip: string;
  dst_ip: string;
  src_port: number;
  dst_port: number;
  protocol: string;
  orig_bytes: number | null;
  resp_bytes: number | null;
  orig_pkts: number | null;
  resp_pkts: number | null;
  conn_state: string | null;
}

// ------------------------------------------------------------------
// Mock Auth / User
// ------------------------------------------------------------------

export interface MockUser {
  id: string;
  name: string;
  email: string;
  role: string;
  avatar_initials: string;
}

export interface MockOrganization {
  id: string;
  name: string;
  plan: string;
}

// ------------------------------------------------------------------
// Display Helpers
// ------------------------------------------------------------------

export const THREAT_TYPE_LABELS: Record<ThreatType, string> = {
  volumetric_ddos: 'Volumetric DDoS',
  c2_beaconing: 'C2 Beaconing',
  dga_dns_tunnel: 'DGA / DNS Tunnel',
  encrypted_malware: 'Encrypted Malware',
  recon_portscan: 'Recon / Port Scan',
  data_exfiltration: 'Data Exfiltration',
};

export const DETECTOR_LABELS: Record<DetectorId, string> = {
  ddos_detector: 'DDoS Detector',
  recon_detector: 'Recon Detector',
  dns_dga_tunnel_detector: 'DNS/DGA Detector',
  tls_c2_detector: 'TLS/C2 Detector',
  exfiltration_detector: 'Exfiltration Detector',
};

export const SEVERITY_ORDER: Severity[] = ['critical', 'high', 'medium', 'low', 'info'];

export const STATUS_LABELS: Record<AlertStatus, string> = {
  new: 'New',
  investigating: 'Investigating',
  closed: 'Closed',
  false_positive: 'False Positive',
};
