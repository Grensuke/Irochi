"""
Alert schemas — Pydantic models for alert presentation.

IMPORTANT: These are PRESENTATION models for the dummy API.
They are NOT canonical event fields. Do not confuse these with
the Canonical Event Schema (docs/data/CANONICAL_EVENT_SCHEMA_FINAL.md).
Derived/windowed features do not belong here either.
"""

from __future__ import annotations

import enum
from datetime import datetime

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Enums — threat taxonomy per IROCHI_INIT_PROMPT.md Section 12
# ------------------------------------------------------------------


class ThreatType(str, enum.Enum):
    """Six threat capabilities shown to users."""

    VOLUMETRIC_DDOS = "volumetric_ddos"
    C2_BEACONING = "c2_beaconing"
    DGA_DNS_TUNNEL = "dga_dns_tunnel"
    ENCRYPTED_MALWARE = "encrypted_malware"
    RECON_PORTSCAN = "recon_portscan"
    DATA_EXFILTRATION = "data_exfiltration"


class DetectorId(str, enum.Enum):
    """Five logical detector modules (NOT microservices)."""

    DDOS_DETECTOR = "ddos_detector"
    RECON_DETECTOR = "recon_detector"
    DNS_DGA_TUNNEL_DETECTOR = "dns_dga_tunnel_detector"
    TLS_C2_DETECTOR = "tls_c2_detector"
    EXFILTRATION_DETECTOR = "exfiltration_detector"


class Severity(str, enum.Enum):
    """Alert severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, enum.Enum):
    """Alert lifecycle status."""

    NEW = "new"
    INVESTIGATING = "investigating"
    CLOSED = "closed"
    FALSE_POSITIVE = "false_positive"


# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------


class AlertResponse(BaseModel):
    """Single alert for API responses."""

    alert_id: str
    timestamp: datetime
    threat_type: ThreatType
    detector_id: DetectorId
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    src_ip: str | None = None
    src_port: int | None = None
    dst_ip: str | None = None
    dst_port: int | None = None
    evidence_summary: str
    status: AlertStatus


class AlertListResponse(BaseModel):
    """Response wrapper for alert list endpoint."""

    alerts: list[AlertResponse]
    total: int


class WebSocketMessage(BaseModel):
    """WebSocket message envelope for alert delivery.

    type = "backfill" → historical alert from simulated database recovery
    type = "live"     → newly arrived alert from simulated live stream
    """

    type: str = Field(pattern=r"^(backfill|live|backfill_complete)$")
    alert: AlertResponse | None = None
