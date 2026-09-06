"""Alert routes — list and detail endpoints."""

from __future__ import annotations
import uuid
from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends

from app.schemas.alerts import AlertListResponse, AlertResponse
from app.services.postgres_alert_service import PostgresAlertService
from app.api.dependencies import get_postgres_alert_service

router = APIRouter()


@router.get(
    "/alerts",
    response_model=AlertListResponse,
    summary="List alerts",
    description="Return alerts. In production, supports filtering and pagination.",
)
async def list_alerts(
    alert_service: Annotated[PostgresAlertService, Depends(get_postgres_alert_service)]
) -> AlertListResponse:
    """Return all alerts."""
    alerts_orm = await alert_service.list_alerts()

    # Map ORM objects to AlertResponse
    alerts = []
    for a in alerts_orm:
        alerts.append(AlertResponse(
            alert_id=str(a.alert_id),
            timestamp=a.last_seen_at,
            threat_type=a.threat_type,
            detector_id=a.detector_id,
            severity=a.severity,
            confidence=a.confidence,
            entity_type=a.entity_type,
            entity_key=a.entity_key,
            first_seen_at=a.first_seen_at,
            last_seen_at=a.last_seen_at,
            resolved_at=a.resolved_at,
            evidence_summary=a.evidence_summary or "",
            status=a.status
        ))

    return AlertListResponse(alerts=alerts, total=len(alerts))


@router.get(
    "/alerts/{alert_id}",
    response_model=AlertResponse,
    summary="Get alert by ID",
    description="Return a single alert by its ID, or 404 if not found.",
)
async def get_alert(
    alert_id: str,
    alert_service: Annotated[PostgresAlertService, Depends(get_postgres_alert_service)]
) -> AlertResponse:
    """Return a single alert by ID."""
    try:
        uid = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid alert ID format")

    alert_orm = await alert_service.get_alert(uid)
    if alert_orm is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    return AlertResponse(
        alert_id=str(alert_orm.alert_id),
        timestamp=alert_orm.last_seen_at,
        threat_type=alert_orm.threat_type,
        detector_id=alert_orm.detector_id,
        severity=alert_orm.severity,
        confidence=alert_orm.confidence or 0.0,
        entity_type=alert_orm.entity_type,
        entity_key=alert_orm.entity_key,
        first_seen_at=alert_orm.first_seen_at,
        last_seen_at=alert_orm.last_seen_at,
        resolved_at=alert_orm.resolved_at,
        evidence_summary=alert_orm.evidence_summary or "",
        status=alert_orm.status
    )
