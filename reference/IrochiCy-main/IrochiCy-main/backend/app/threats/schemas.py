"""Threat intelligence Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

from app.alerts.schemas import AlertResponse


class SignalDefinition(BaseModel):
    name: str
    signal_type: Literal["raw", "derived", "intel"]
    description: str
    threshold: Optional[str] = None
    weight: float


class ThreatTypeStat(BaseModel):
    threat_type: str
    display_name: str
    description: str
    signals: list[SignalDefinition]
    alerts_today: int
    alerts_7d: int
    avg_confidence: float
    detector_status: Literal["running", "idle", "error"]
    last_detection: Optional[datetime]


class ConfidenceBucket(BaseModel):
    bucket_label: str
    count: int


class ThreatDetailResponse(BaseModel):
    threat_type: str
    stat: ThreatTypeStat
    confidence_distribution: list[ConfidenceBucket]
    recent_alerts: list[AlertResponse]
