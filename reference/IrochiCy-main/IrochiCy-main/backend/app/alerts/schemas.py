"""Alerts Pydantic schemas for request/response validation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ── Evidence ─────────────────────────────────────────────────────

class EvidenceItem(BaseModel):
    signal_name: str
    signal_type: Literal["raw", "derived", "intel"]
    value: Any
    threshold: Optional[float] = None
    triggered: bool


# ── Enums as literals ────────────────────────────────────────────

THREAT_TYPES = ("ddos", "recon", "dns_dga", "tls_c2", "exfiltration")
SEVERITY_LEVELS = ("low", "medium", "high", "critical")
ALERT_STATUSES = ("new", "acknowledged", "investigating", "escalated", "closed")


# ── Responses ────────────────────────────────────────────────────

class AlertResponse(BaseModel):
    id: UUID
    threat_type: str
    severity: str
    confidence: float
    src_ip: str
    dst_ip: str
    src_port: Optional[int]
    dst_port: Optional[int]
    protocol: Optional[str]
    detector_id: str
    schema_version: str
    sensor_source: Optional[str]
    evidence: list[EvidenceItem]
    status: str
    assigned_to: Optional[UUID]
    analyst_notes: Optional[str]
    raw_event_id: Optional[UUID]
    ingest_latency_ms: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("evidence", mode="before")
    @classmethod
    def coerce_evidence(cls, v: Any) -> list:
        """Accept raw dicts/lists from the DB JSONB column."""
        if v is None:
            return []
        if isinstance(v, str):
            import json
            return json.loads(v)
        if isinstance(v, list):
            return v
        return []

    @field_validator("src_ip", "dst_ip", mode="before")
    @classmethod
    def coerce_ip(cls, v: Any) -> str:
        """Convert asyncpg IPv4Address objects to string."""
        return str(v)


class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


# ── Mutations ────────────────────────────────────────────────────

class AlertStatusUpdate(BaseModel):
    status: Literal["acknowledged", "investigating", "escalated", "closed"]
    note: Optional[str] = None


# ── Filters ──────────────────────────────────────────────────────

class AlertFilters(BaseModel):
    threat_type: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    search: Optional[str] = None
    after: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(25, ge=1, le=100)

    @field_validator("threat_type")
    @classmethod
    def validate_threat_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in THREAT_TYPES:
            raise ValueError(f"threat_type must be one of {THREAT_TYPES}")
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in SEVERITY_LEVELS:
            raise ValueError(f"severity must be one of {SEVERITY_LEVELS}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALERT_STATUSES:
            raise ValueError(f"status must be one of {ALERT_STATUSES}")
        return v
