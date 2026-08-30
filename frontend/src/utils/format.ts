import type { Severity, ThreatType, DetectorId } from '../types';
import { THREAT_TYPE_LABELS, DETECTOR_LABELS } from '../types';

/* ── Severity helpers ─────────────────────────────── */

export function severityColor(severity: Severity): string {
  return `var(--severity-${severity})`;
}

export function confidenceColor(confidence: number | null): string {
  if (confidence === null) return 'var(--text-dim)';
  if (confidence >= 0.85) return 'var(--severity-critical)';
  if (confidence >= 0.70) return 'var(--severity-high)';
  if (confidence >= 0.50) return 'var(--severity-medium)';
  return 'var(--severity-low)';
}

/* ── Formatting ─────────────────────────────────── */

export function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}

export function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

export function formatConfidence(value: number | null): string {
  if (value === null) return '—';
  return `${(value * 100).toFixed(0)}%`;
}

export function threatLabel(type: ThreatType): string {
  return THREAT_TYPE_LABELS[type] ?? type;
}

export function detectorLabel(id: DetectorId): string {
  return DETECTOR_LABELS[id] ?? id;
}

export function timeAgo(iso: string): string {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

/* ── Byte/Rate Helpers ─────────────────────────────── */

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1073741824) return `${(bytes / 1048576).toFixed(1)} MB`;
  return `${(bytes / 1073741824).toFixed(2)} GB`;
}

export function formatRate(bitsPerSecond: number): string {
  if (bitsPerSecond < 1000) return `${bitsPerSecond} bps`;
  if (bitsPerSecond < 1_000_000) return `${(bitsPerSecond / 1000).toFixed(1)} Kbps`;
  if (bitsPerSecond < 1_000_000_000) return `${(bitsPerSecond / 1_000_000).toFixed(1)} Mbps`;
  return `${(bitsPerSecond / 1_000_000_000).toFixed(2)} Gbps`;
}
