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
  | 'exfiltration_detector'
  | 'anomaly_detector';

/** Six threat capabilities shown to users. */
export type ThreatType =
  | 'volumetric_ddos'
  | 'c2_beaconing'
  | 'dga_dns_tunnel'
  | 'encrypted_malware'
  | 'recon_portscan'
  | 'data_exfiltration'
  | 'novel_anomaly';

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
  incident_id?: string | null;
  detector_output_id?: string | null;
  timestamp: string;
  threat_type: ThreatType;
  detector_id: DetectorId;
  severity: Severity;
  severity_candidate?: string | null;
  confidence: number | null;
  entity_type: 'source' | 'destination' | 'pair' | 'connection';
  entity_key: string;
  detected_at?: string | null;
  created_at?: string | null;
  first_seen_at: string;
  last_seen_at: string;
  resolved_at?: string | null;
  src_ip: string | null;
  src_port?: number | null;
  dst_ip: string | null;
  dst_port?: number | null;
  title?: string | null;
  evidence_summary: string;
  evidence?: Record<string, any> | null;
  source_feature_references?: Record<string, any>[] | null;
  score?: number | null;
  status: AlertStatus;
  detector_version?: string | null;
  model_version?: string | null;
  schema_version?: string | null;
}

// ------------------------------------------------------------------
// API Responses
// ------------------------------------------------------------------

export interface AlertListResponse {
  alerts: Alert[];
  total: number;
}

// ------------------------------------------------------------------
// Incident
// ------------------------------------------------------------------

export interface Incident {
  incident_id: string;
  entity_type: string;
  entity_key: string;
  status: 'open' | 'closed';
  opened_at: string;
  updated_at: string;
  last_event_at: string;
  member_alert_ids: string[];
  distinct_threat_types: ThreatType[];
  risk_score: number;
  risk_breakdown: Record<string, number>;
  stage_state: 'anomaly' | 'suspicious' | 'likely_attack' | 'confirmed_attack';
  current_stage?: string | null;
  forecast_next_stage?: string | null;
  forecast_note?: string | null;
  schema_version: string;
}

export interface IncidentListResponse {
  incidents: Incident[];
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
  novel_anomaly: 'Novel Anomaly',
};

export const DETECTOR_LABELS: Record<DetectorId, string> = {
  ddos_detector: 'DDoS Detector',
  recon_detector: 'Recon Detector',
  dns_dga_tunnel_detector: 'DNS/DGA Detector',
  tls_c2_detector: 'TLS/C2 Detector',
  exfiltration_detector: 'Exfiltration Detector',
  anomaly_detector: 'Anomaly Detector',
};

export const SEVERITY_ORDER: Severity[] = ['critical', 'high', 'medium', 'low', 'info'];

export const STATUS_LABELS: Record<AlertStatus, string> = {
  new: 'New',
  investigating: 'Investigating',
  closed: 'Closed',
  false_positive: 'False Positive',
};
