"""DetectorResult Pydantic model — output schema for all detectors."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    """A single piece of evidence supporting a detection."""

    signal_name: str
    signal_type: Literal["raw", "derived", "intel"]
    value: Any
    threshold: Optional[float] = None
    triggered: bool


class DetectorResult(BaseModel):
    """Result emitted by a detector when a threat is identified."""

    event_id: str
    threat_type: Literal["ddos", "recon", "dns_dga", "tls_c2", "exfiltration"]
    detector_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[EvidenceItem]
    src_ip: str
    dst_ip: str
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    protocol: Optional[str] = None
    sensor_source: Optional[str] = None
    schema_version: str = "1.0.0"
    detected_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
