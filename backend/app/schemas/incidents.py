"""
Incident schemas — Pydantic models for incident presentation.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.alerts import ThreatType


class IncidentCloseRequest(BaseModel):
    resolution_note: str | None = None
    closed_by: str | None = None


class IncidentResponse(BaseModel):
    """Single incident for API responses."""

    incident_id: str
    entity_type: str
    entity_key: str
    status: str
    opened_at: datetime
    updated_at: datetime
    last_event_at: datetime
    member_alert_ids: list[str]
    distinct_threat_types: list[ThreatType]
    risk_score: float
    risk_breakdown: dict[str, float]
    stage_state: str
    current_stage: str | None = None
    forecast_next_stage: str | None = None
    forecast_note: str | None = None
    closed_at: datetime | None = None
    closed_by: str | None = None
    resolution_note: str | None = None
    schema_version: str

    @classmethod
    def from_orm(cls, obj: Any) -> "IncidentResponse":
        return cls.model_construct(
            incident_id=str(obj.incident_id),
            entity_type=obj.entity_type,
            entity_key=obj.entity_key,
            status=obj.status,
            opened_at=obj.opened_at,
            updated_at=obj.updated_at,
            last_event_at=obj.last_event_at,
            member_alert_ids=obj.member_alert_ids,
            distinct_threat_types=[ThreatType(t) for t in obj.distinct_threat_types],
            risk_score=obj.risk_score,
            risk_breakdown=obj.risk_breakdown,
            stage_state=obj.stage_state,
            current_stage=obj.current_stage,
            forecast_next_stage=obj.forecast_next_stage,
            forecast_note=obj.forecast_note,
            closed_at=obj.closed_at,
            closed_by=obj.closed_by,
            resolution_note=obj.resolution_note,
            schema_version=obj.schema_version,
        )


class IncidentListResponse(BaseModel):
    """Response wrapper for incident list endpoint."""

    incidents: list[IncidentResponse]
    total: int
