"""
Alert ORM model mapping the persisted fields of the approved logical model.
Derived/logical fields such as `dedup_identity` are not separate ORM columns.
`dedup_digest` is not implemented.
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


class Alert(Base):
    __tablename__ = "alerts"

    # Implementation Guardrail: entity_type = source | destination | pair | connection
    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('source', 'destination', 'pair', 'connection')",
            name="chk_valid_entity_type"
        ),
        CheckConstraint(
            "status IN ('new', 'investigating', 'closed', 'false_positive')",
            name="chk_valid_status"
        ),
    )

    alert_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    detector_output_id: Mapped[str] = mapped_column(String, nullable=False)

    detector_id: Mapped[str] = mapped_column(String, nullable=False)
    threat_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_key: Mapped[str] = mapped_column(String, nullable=False)

    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    status: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    severity_candidate: Mapped[str] = mapped_column(String, nullable=False)

    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)

    title: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_summary: Mapped[str] = mapped_column(Text, nullable=False)

    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    source_feature_references: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)

    detector_version: Mapped[str] = mapped_column(String, nullable=False)
    model_version: Mapped[str | None] = mapped_column(String, nullable=True)
    schema_version: Mapped[str] = mapped_column(String, nullable=False)

    update_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
