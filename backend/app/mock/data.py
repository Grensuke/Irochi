"""
Realistic mock alert data covering all six threat capabilities.

IMPORTANT:
- These are PRESENTATION alert records for the dummy API.
- They are NOT canonical event records.
- Derived/feature fields do NOT belong here.
- Do not add these fields to the Canonical Event Schema.

Threat taxonomy (Section 12 of init prompt):

  Detector Modules (5):
    ddos_detector, recon_detector, dns_dga_tunnel_detector,
    tls_c2_detector, exfiltration_detector

  Threat Capabilities (6):
    volumetric_ddos, c2_beaconing, dga_dns_tunnel,
    encrypted_malware, recon_portscan, data_exfiltration

One detector module may emit multiple threat classes.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.alerts import (
    AlertResponse,
    AlertStatus,
    DetectorId,
    Severity,
    ThreatType,
)


def _ts(iso: str) -> datetime:
    """Parse an ISO timestamp string to a timezone-aware datetime."""
    return datetime.fromisoformat(iso)


# ------------------------------------------------------------------
# Static mock alerts — deterministic for frontend development
# ------------------------------------------------------------------

MOCK_ALERTS: list[AlertResponse] = [
    # 1 — Volumetric DDoS (critical)
    AlertResponse(
        alert_id="ALERT-001",
        timestamp=_ts("2026-08-27T14:23:11+00:00"),
        threat_type=ThreatType.VOLUMETRIC_DDOS,
        detector_id=DetectorId.DDOS_DETECTOR,
        severity=Severity.CRITICAL,
        confidence=0.96,
        src_ip="198.51.100.0/24",
        dst_ip="10.0.5.20",
        dst_port=80,
        evidence_summary=(
            "SYN flood detected: ~12,400 SYN packets/sec from distributed "
            "sources targeting 10.0.5.20:80. syn_ratio 0.98, source entropy "
            "elevated. Multiple /24 source prefixes observed."
        ),
        status=AlertStatus.NEW,
    ),
    # 2 — C2 Beaconing (high)
    AlertResponse(
        alert_id="ALERT-002",
        timestamp=_ts("2026-08-27T14:18:45+00:00"),
        threat_type=ThreatType.C2_BEACONING,
        detector_id=DetectorId.TLS_C2_DETECTOR,
        severity=Severity.HIGH,
        confidence=0.89,
        src_ip="10.0.2.15",
        src_port=49210,
        dst_ip="203.0.113.47",
        dst_port=443,
        evidence_summary=(
            "Periodic outbound TLS connections to 203.0.113.47:443 every "
            "~60±2s over 45 min. Low payload variance. Inter-arrival-time "
            "periodicity score 0.94. JA3 hash not in SSLBL but connection "
            "pattern consistent with beacon behaviour."
        ),
        status=AlertStatus.INVESTIGATING,
    ),
    # 3 — DGA / DNS Tunneling (high)
    AlertResponse(
        alert_id="ALERT-003",
        timestamp=_ts("2026-08-27T14:15:32+00:00"),
        threat_type=ThreatType.DGA_DNS_TUNNEL,
        detector_id=DetectorId.DNS_DGA_TUNNEL_DETECTOR,
        severity=Severity.HIGH,
        confidence=0.92,
        src_ip="10.0.3.42",
        dst_ip="8.8.8.8",
        dst_port=53,
        evidence_summary=(
            "High-entropy DNS queries to 47 unique subdomains of "
            "xk3m9.example.net in 5 min. domain_entropy 4.7, avg label "
            "length 24, query_frequency 9.4/sec. Pattern consistent with "
            "DGA-generated domains or DNS tunneling."
        ),
        status=AlertStatus.NEW,
    ),
    # 4 — Encrypted-session malware (medium)
    AlertResponse(
        alert_id="ALERT-004",
        timestamp=_ts("2026-08-27T14:10:08+00:00"),
        threat_type=ThreatType.ENCRYPTED_MALWARE,
        detector_id=DetectorId.TLS_C2_DETECTOR,
        severity=Severity.MEDIUM,
        confidence=0.72,
        src_ip="10.0.4.88",
        src_port=51433,
        dst_ip="192.0.2.199",
        dst_port=443,
        evidence_summary=(
            "JA3 fingerprint 'a0e9f5d6...' matched SSLBL blacklist entry "
            "associated with Emotet malware family. Single TLS session to "
            "192.0.2.199:443. ja3_blacklist_match is a medium-confidence "
            "supporting signal — requires corroboration."
        ),
        status=AlertStatus.NEW,
    ),
    # 5 — Reconnaissance / Port Scanning (medium)
    AlertResponse(
        alert_id="ALERT-005",
        timestamp=_ts("2026-08-27T14:05:22+00:00"),
        threat_type=ThreatType.RECON_PORTSCAN,
        detector_id=DetectorId.RECON_DETECTOR,
        severity=Severity.MEDIUM,
        confidence=0.85,
        src_ip="10.0.1.200",
        dst_ip="10.0.5.0/24",
        evidence_summary=(
            "Horizontal port scan: 10.0.1.200 probed 312 unique destination "
            "ports across 10.0.5.0/24 in 90 seconds. SYN-only connections "
            "with no established sessions. scan_rate 3.5 ports/sec."
        ),
        status=AlertStatus.RESOLVED,
    ),
    # 6 — Data Exfiltration (critical)
    AlertResponse(
        alert_id="ALERT-006",
        timestamp=_ts("2026-08-27T13:58:15+00:00"),
        threat_type=ThreatType.DATA_EXFILTRATION,
        detector_id=DetectorId.EXFILTRATION_DETECTOR,
        severity=Severity.CRITICAL,
        confidence=0.88,
        src_ip="10.0.2.77",
        src_port=44892,
        dst_ip="198.51.100.55",
        dst_port=443,
        evidence_summary=(
            "Sustained large outbound transfer: 2.3 GB over 18 min to "
            "198.51.100.55:443. outbound_inbound_ratio 47:1. Transfer "
            "volume anomalous for this host's 30-day baseline."
        ),
        status=AlertStatus.NEW,
    ),
    # 7 — DDoS (low severity — informational spike)
    AlertResponse(
        alert_id="ALERT-007",
        timestamp=_ts("2026-08-27T13:52:40+00:00"),
        threat_type=ThreatType.VOLUMETRIC_DDOS,
        detector_id=DetectorId.DDOS_DETECTOR,
        severity=Severity.LOW,
        confidence=0.55,
        src_ip="192.0.2.0/24",
        dst_ip="10.0.5.20",
        dst_port=443,
        evidence_summary=(
            "Moderate UDP traffic spike from 192.0.2.0/24 to 10.0.5.20:443. "
            "byte_rate elevated 2.1× above 1h baseline. Below volumetric "
            "threshold but flagged for monitoring."
        ),
        status=AlertStatus.RESOLVED,
    ),
    # 8 — DNS tunneling (medium)
    AlertResponse(
        alert_id="ALERT-008",
        timestamp=_ts("2026-08-27T13:45:18+00:00"),
        threat_type=ThreatType.DGA_DNS_TUNNEL,
        detector_id=DetectorId.DNS_DGA_TUNNEL_DETECTOR,
        severity=Severity.MEDIUM,
        confidence=0.78,
        src_ip="10.0.3.15",
        dst_ip="10.0.0.1",
        dst_port=53,
        evidence_summary=(
            "TXT record queries with encoded payloads to "
            "data.tunnel-c2.example.org. Average query length 180 chars. "
            "Consistent with DNS tunneling data exfiltration channel."
        ),
        status=AlertStatus.INVESTIGATING,
    ),
    # 9 — Recon (low)
    AlertResponse(
        alert_id="ALERT-009",
        timestamp=_ts("2026-08-27T13:38:55+00:00"),
        threat_type=ThreatType.RECON_PORTSCAN,
        detector_id=DetectorId.RECON_DETECTOR,
        severity=Severity.LOW,
        confidence=0.62,
        src_ip="10.0.1.150",
        dst_ip="10.0.5.10",
        evidence_summary=(
            "Vertical port scan: 10.0.1.150 probed 42 ports on 10.0.5.10 "
            "over 3 min. Mostly high-numbered ports. Lower confidence — "
            "may be legitimate service discovery."
        ),
        status=AlertStatus.FALSE_POSITIVE,
    ),
    # 10 — C2 beaconing (info — resolved)
    AlertResponse(
        alert_id="ALERT-010",
        timestamp=_ts("2026-08-27T13:30:00+00:00"),
        threat_type=ThreatType.C2_BEACONING,
        detector_id=DetectorId.TLS_C2_DETECTOR,
        severity=Severity.INFO,
        confidence=0.45,
        src_ip="10.0.4.22",
        src_port=55120,
        dst_ip="203.0.113.10",
        dst_port=8443,
        evidence_summary=(
            "Periodic HTTPS connections to 203.0.113.10:8443 every ~300s. "
            "Pattern resembles keepalive or health-check. Low confidence "
            "of malicious C2 — likely benign application polling."
        ),
        status=AlertStatus.RESOLVED,
    ),
    # 11 — Exfiltration (high)
    AlertResponse(
        alert_id="ALERT-011",
        timestamp=_ts("2026-08-27T13:22:33+00:00"),
        threat_type=ThreatType.DATA_EXFILTRATION,
        detector_id=DetectorId.EXFILTRATION_DETECTOR,
        severity=Severity.HIGH,
        confidence=0.82,
        src_ip="10.0.2.91",
        src_port=38750,
        dst_ip="198.51.100.120",
        dst_port=22,
        evidence_summary=(
            "Large SSH transfer: 890 MB outbound to 198.51.100.120:22 "
            "over 12 min. outbound_inbound_ratio 38:1. Destination IP "
            "not in known infrastructure list."
        ),
        status=AlertStatus.NEW,
    ),
    # 12 — Encrypted malware (high)
    AlertResponse(
        alert_id="ALERT-012",
        timestamp=_ts("2026-08-27T13:15:10+00:00"),
        threat_type=ThreatType.ENCRYPTED_MALWARE,
        detector_id=DetectorId.TLS_C2_DETECTOR,
        severity=Severity.HIGH,
        confidence=0.84,
        src_ip="10.0.4.55",
        src_port=49876,
        dst_ip="203.0.113.88",
        dst_port=443,
        evidence_summary=(
            "JA3 fingerprint 'b3c4e7f8...' matched SSLBL entry linked to "
            "TrickBot. Connection followed by periodic beaconing at 120s "
            "intervals. Combined JA3 match + beacon pattern raises "
            "confidence above single-signal threshold."
        ),
        status=AlertStatus.INVESTIGATING,
    ),
]


# ------------------------------------------------------------------
# Index for O(1) lookup by alert_id
# ------------------------------------------------------------------

MOCK_ALERTS_BY_ID: dict[str, AlertResponse] = {
    alert.alert_id: alert for alert in MOCK_ALERTS
}


# ------------------------------------------------------------------
# Templates for generating additional live alerts
# ------------------------------------------------------------------

LIVE_ALERT_TEMPLATES: list[dict] = [
    {
        "threat_type": ThreatType.VOLUMETRIC_DDOS,
        "detector_id": DetectorId.DDOS_DETECTOR,
        "severity": Severity.HIGH,
        "confidence": 0.91,
        "src_ip": "203.0.113.0/24",
        "dst_ip": "10.0.5.20",
        "dst_port": 80,
        "evidence_summary": (
            "New SYN flood wave detected from 203.0.113.0/24 targeting "
            "10.0.5.20:80. Packet rate escalating."
        ),
    },
    {
        "threat_type": ThreatType.C2_BEACONING,
        "detector_id": DetectorId.TLS_C2_DETECTOR,
        "severity": Severity.MEDIUM,
        "confidence": 0.74,
        "src_ip": "10.0.2.30",
        "dst_ip": "198.51.100.77",
        "dst_port": 8080,
        "evidence_summary": (
            "New beacon pattern detected: 10.0.2.30 → 198.51.100.77:8080 "
            "with 90s interval. Monitoring for persistence."
        ),
    },
    {
        "threat_type": ThreatType.DGA_DNS_TUNNEL,
        "detector_id": DetectorId.DNS_DGA_TUNNEL_DETECTOR,
        "severity": Severity.HIGH,
        "confidence": 0.87,
        "src_ip": "10.0.3.60",
        "dst_ip": "8.8.4.4",
        "dst_port": 53,
        "evidence_summary": (
            "Burst of high-entropy A queries: 23 unique subdomains of "
            "r8kq2.example.com in 60 seconds. DGA confidence elevated."
        ),
    },
    {
        "threat_type": ThreatType.RECON_PORTSCAN,
        "detector_id": DetectorId.RECON_DETECTOR,
        "severity": Severity.MEDIUM,
        "confidence": 0.79,
        "src_ip": "10.0.1.180",
        "dst_ip": "10.0.6.0/24",
        "evidence_summary": (
            "Network sweep: 10.0.1.180 probing SSH (22) and RDP (3389) "
            "across 10.0.6.0/24. 48 hosts contacted in 2 min."
        ),
    },
    {
        "threat_type": ThreatType.DATA_EXFILTRATION,
        "detector_id": DetectorId.EXFILTRATION_DETECTOR,
        "severity": Severity.HIGH,
        "confidence": 0.86,
        "src_ip": "10.0.2.44",
        "dst_ip": "192.0.2.200",
        "dst_port": 443,
        "evidence_summary": (
            "Sustained HTTPS upload: 450 MB in 8 min to 192.0.2.200. "
            "outbound_inbound_ratio 52:1. Anomalous for this endpoint."
        ),
    },
    {
        "threat_type": ThreatType.ENCRYPTED_MALWARE,
        "detector_id": DetectorId.TLS_C2_DETECTOR,
        "severity": Severity.MEDIUM,
        "confidence": 0.68,
        "src_ip": "10.0.4.102",
        "dst_ip": "203.0.113.199",
        "dst_port": 443,
        "evidence_summary": (
            "JA3 fingerprint 'c5d6e8f9...' partial match against SSLBL "
            "Dridex entry. Single session — monitoring for recurrence."
        ),
    },
]
