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

from typing import Any

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
    NOVEL_ANOMALY = "novel_anomaly"


class DetectorId(str, enum.Enum):
    """Five logical detector modules (NOT microservices)."""

    DDOS_DETECTOR = "ddos_detector"
    RECON_DETECTOR = "recon_detector"
    DNS_DGA_TUNNEL_DETECTOR = "dns_dga_tunnel_detector"
    TLS_C2_DETECTOR = "tls_c2_detector"
    EXFILTRATION_DETECTOR = "exfiltration_detector"
    ANOMALY_DETECTOR = "anomaly_detector"


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
    incident_id: str | None = None
    detector_output_id: str | None = None
    timestamp: datetime
    threat_type: ThreatType
    detector_id: DetectorId
    severity: Severity
    severity_candidate: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    entity_type: str
    entity_key: str
    detected_at: datetime | None = None
    created_at: datetime | None = None
    first_seen_at: datetime
    last_seen_at: datetime
    resolved_at: datetime | None = None
    src_ip: str | None = None
    src_port: int | None = None
    dst_ip: str | None = None
    dst_port: int | None = None
    title: str | None = None
    evidence_summary: str
    evidence: dict | None = None
    source_feature_references: list[dict[str, Any]] | None = None
    score: float | None = None
    status: AlertStatus
    detector_version: str | None = None
    model_version: str | None = None
    schema_version: str | None = None

    @classmethod
    def from_orm(cls, obj: Any) -> "AlertResponse":
        """
        Creates an AlertResponse from a database Alert ORM object.
        Derives src_ip, dst_ip, src_port, dst_port according to the data contract.
        """
        src_ip = None
        dst_ip = None
        src_port = None
        dst_port = None

        if obj.entity_type == "source":
            src_ip = obj.entity_key
        elif obj.entity_type == "destination":
            dst_ip = obj.entity_key
        elif obj.entity_type == "pair" and "|" in obj.entity_key:
            parts = obj.entity_key.split("|")
            if len(parts) == 2:
                src_ip, dst_ip = parts[0], parts[1]
        
        # Extract from evidence.alert_context if present
        if obj.evidence and isinstance(obj.evidence, dict):
            ctx = obj.evidence.get("alert_context", {})
            if isinstance(ctx, dict):
                src_ip = ctx.get("src_ip", src_ip)
                dst_ip = ctx.get("dst_ip", dst_ip)
                src_port = ctx.get("src_port", src_port)
                dst_port = ctx.get("dst_port", dst_port)

        return cls.model_construct(
            alert_id=str(obj.alert_id),
            incident_id=str(obj.incident_id) if getattr(obj, "incident_id", None) else None,
            detector_output_id=getattr(obj, "detector_output_id", None),
            timestamp=obj.last_seen_at,
            threat_type=obj.threat_type,
            detector_id=obj.detector_id,
            severity=obj.severity,
            severity_candidate=getattr(obj, "severity_candidate", None),
            confidence=obj.confidence or 0.0,
            entity_type=obj.entity_type,
            entity_key=obj.entity_key,
            detected_at=getattr(obj, "detected_at", None),
            created_at=getattr(obj, "created_at", None),
            first_seen_at=obj.first_seen_at,
            last_seen_at=obj.last_seen_at,
            resolved_at=obj.resolved_at,
            src_ip=src_ip,
            src_port=src_port,
            dst_ip=dst_ip,
            dst_port=dst_port,
            title=getattr(obj, "title", None),
            evidence_summary=obj.evidence_summary or "",
            evidence=obj.evidence,
            source_feature_references=getattr(obj, "source_feature_references", None),
            score=obj.score,
            status=obj.status,
            detector_version=getattr(obj, "detector_version", None),
            model_version=getattr(obj, "model_version", None),
            schema_version=getattr(obj, "schema_version", None)
        )


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
