/* ═══════════════════════════════════════════════════════════════
   SIH-26145 TypeScript Interfaces
   Core domain types for the threat-detection platform
   ═══════════════════════════════════════════════════════════════ */

// ─── Theme ───
export type ThemeMode = 'dark' | 'light';

// ─── Auth ───
export interface User {
  id: string;
  username: string;
  role: 'ANALYST' | 'ADMIN';
  displayName: string;
  initials: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

// ─── Threat Types ───
export type ThreatType = 'ddos' | 'recon' | 'dns' | 'tls' | 'exfil';

export const THREAT_LABELS: Record<ThreatType, string> = {
  ddos: 'DDoS',
  recon: 'Recon',
  dns: 'DNS-DGA',
  tls: 'TLS-C2',
  exfil: 'Exfil',
};

// ─── Severity ───
export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';

export const SEVERITY_LABELS: Record<Severity, string> = {
  critical: 'CRITICAL',
  high: 'HIGH',
  medium: 'MEDIUM',
  low: 'LOW',
  info: 'INFO',
};

// ─── Alert ───
export type AlertStatus = 'new' | 'acknowledged' | 'investigating' | 'closed' | 'escalated';

export interface Alert {
  alert_id: string;
  threat_type: ThreatType;
  severity: Severity;
  src_ip: string;
  dst_ip: string;
  src_port: number;
  dst_port: number;
  protocol: 'TCP' | 'UDP' | 'ICMP' | 'OTHER';
  confidence: number; // 0.0 – 1.0
  evidence: Evidence[];
  status: AlertStatus;
  created_at: string; // ISO 8601
  detector_id: string;
  flagged_src?: boolean;
  flagged_dst?: boolean;
  threat_name?: string;
  notes?: AnalystNote[];
  assigned_to?: string;
  canonical_event?: CanonicalEvent;
}

export interface Evidence {
  type: string;
  description: string;
  value: string | number;
}

// ─── Canonical Event ───
export interface CanonicalEvent {
  event_id: string;
  event_type: 'connection' | 'dns' | 'tls';
  ingest_timestamp: number; // epoch µs
  sensor_source: 'zeek' | 'netflow' | 'ipfix' | 'sflow';
  src_ip: string;
  dst_ip: string;
  src_port: number;
  dst_port: number;
  protocol: 'TCP' | 'UDP' | 'ICMP' | 'OTHER';
  schema_version: string;
}

// ─── Detector Result ───
export interface DetectorResult {
  threat_type: ThreatType;
  confidence: number;
  detector_id: string;
  evidence: Evidence[];
}

// ─── Dashboard ───
export interface KPIData {
  label: string;
  value: number;
  delta: number;
  deltaLabel: string;
  deltaDirection: 'up' | 'down' | 'flat';
  borderColor?: string;
  showPulse?: boolean;
}

export interface TimelineBucket {
  hour: string; // "00:00", "01:00", etc.
  ddos: number;
  recon: number;
  dns: number;
  tls: number;
  exfil: number;
}

export interface DashboardSummary {
  totalAlertsToday: number;
  totalAlertsDelta: number;
  activeThreats: number;
  activeThreatsDelta: number;
  eventsPerSec: number;
  detectorsActive: number;
  detectorStatuses: DetectorStatusInfo[];
  pipelineLatencyMs: number;
}

export interface DetectorStatusInfo {
  id: string;
  name: string;
  threatType: ThreatType;
  status: 'running' | 'idle' | 'error';
  lastDetection: string; // ISO 8601
  alertsToday: number;
  confidence: number; // average confidence 0-1
}

export interface ProtocolBreakdown {
  protocol: string;
  count: number;
  percentage: number;
  color: string;
}

export interface TopSourceIP {
  rank: number;
  ip: string;
  eventCount: number;
  country: string;
  countryCode: string;
}

// ─── WebSocket ───
export type WebSocketStatus = 'connecting' | 'live' | 'reconnecting' | 'offline';

export interface WebSocketMessage {
  type: 'alert' | 'kpi_update' | 'detector_status';
  payload: Alert | Partial<DashboardSummary> | DetectorStatusInfo;
  timestamp: string;
}

// ─── Network ───
export interface NetworkFlow {
  id: string;
  src_ip: string;
  src_port: number;
  dst_ip: string;
  dst_port: number;
  protocol: 'TCP' | 'UDP' | 'ICMP' | 'OTHER';
  bytes_sent: number;
  bytes_recv: number;
  duration: number; // seconds
  conn_state: ConnStateCode;
  event_type: ThreatType | 'normal';
  timestamp: string;
  suspicious: boolean;
}

export type ConnStateCode = 'SF' | 'S0' | 'REJ' | 'RSTO' | 'RSTOS0' | 'RSTRH' | 'SH' | 'SHR' | 'OTH' | 'S1' | 'S2' | 'S3';

export interface ConnStateInfo {
  code: ConnStateCode;
  name: string;
  count: number;
  color: string;
}

// ─── Analyst Notes ───
export interface AnalystNote {
  id: string;
  author: string;
  content: string;
  created_at: string;
}

// ─── Toast ───
export type ToastType = 'info' | 'success' | 'warning' | 'error';

export interface ToastMessage {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  severity?: Severity;
  duration?: number; // ms, default 6000
}

// ─── Sort ───
export type AlertSortField = 'created_at' | 'severity' | 'confidence';
export type SortDirection = 'asc' | 'desc';

export interface AlertSortOption {
  label: string;
  field: AlertSortField;
  direction: SortDirection;
}

// ─── Threat Names ───
export const THREAT_FULL_NAMES: Record<ThreatType, string> = {
  ddos: 'Distributed Denial of Service',
  recon: 'Network Reconnaissance',
  dns: 'DGA Domain Detection',
  tls: 'TLS Command & Control',
  exfil: 'Data Exfiltration',
};

// ─── User Preferences ───
export type TableDensity = 'compact' | 'comfortable' | 'spacious';
export type TimestampFormat = 'relative' | 'absolute';
export type FontScale = 'small' | 'default' | 'large';

export interface UserPreferences {
  theme: ThemeMode;
  tableDensity: TableDensity;
  timestampFormat: TimestampFormat;
  fontScale: FontScale;
  notifyCritical: boolean;
  notifyHigh: boolean;
  notifyReconnect: boolean;
  notifyDailySummary: boolean;
  dailySummaryEmail: string;
}

// ─── Detector Signals ───
export type SignalType = 'raw' | 'derived' | 'intel';

export interface DetectorSignal {
  name: string;
  signalType: SignalType;
  threshold: string;
  weight: number; // 0-1
  triggeredToday: number;
}

export interface ConfidenceBucket {
  range: string; // "0-10%", "10-20%", ...
  count: number;
}

// ─── System / Admin ───
export type ServiceHealth = 'healthy' | 'degraded' | 'down';

export interface SystemService {
  name: string;
  status: ServiceHealth;
  metric: string;
  metricValue: string;
  lastChecked: string;
}

export interface AdminUser {
  id: string;
  username: string;
  displayName: string;
  initials: string;
  role: 'ANALYST' | 'ADMIN';
  status: 'active' | 'suspended';
  lastLogin: string;
  email: string;
}
