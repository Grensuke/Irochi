"""Alert engine Pydantic schemas for Redpanda/Kafka messages."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.alerts.schemas import EvidenceItem


class DetectorResult(BaseModel):
    """Schema for messages consumed from the Redpanda detector.results topic."""

    event_id: UUID
    threat_type: str
    detector_id: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    src_ip: str
    dst_ip: str
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    protocol: Optional[str] = None
    sensor_source: Optional[str] = None
    schema_version: str = "1.0"
    detected_at: datetime
