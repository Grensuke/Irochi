"""
Incident ORM model for Cross-Detector Risk Fusion and Early-Warning.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Incident(Base):
    __tablename__ = "incidents"

    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'closed')",
            name="chk_valid_incident_status"
        ),
        CheckConstraint(
            "stage_state IN ('anomaly', 'suspicious', 'likely_attack', 'confirmed_attack')",
            name="chk_valid_stage_state"
        ),
    )

    incident_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_key: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)

    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    member_alert_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    distinct_threat_types: Mapped[list[str]] = mapped_column(JSONB, nullable=False)

    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_breakdown: Mapped[dict[str, float]] = mapped_column(JSONB, nullable=False)

    stage_state: Mapped[str] = mapped_column(String, nullable=False)
    current_stage: Mapped[str | None] = mapped_column(String, nullable=True)
    forecast_next_stage: Mapped[str | None] = mapped_column(String, nullable=True)
    forecast_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by: Mapped[str | None] = mapped_column(String, nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    schema_version: Mapped[str] = mapped_column(String, nullable=False, default="1.0.0")
