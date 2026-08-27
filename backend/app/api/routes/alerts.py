"""Alert routes — list and detail endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.alerts import AlertListResponse, AlertResponse
from app.services.alert_service import alert_service

router = APIRouter()


@router.get(
    "/alerts",
    response_model=AlertListResponse,
    summary="List alerts",
    description="Return all mock alerts. In production, supports filtering and pagination.",
)
def list_alerts() -> AlertListResponse:
    """Return all mock alerts."""
    alerts = alert_service.get_alerts()
    return AlertListResponse(alerts=alerts, total=len(alerts))


@router.get(
    "/alerts/{alert_id}",
    response_model=AlertResponse,
    summary="Get alert by ID",
    description="Return a single alert by its ID, or 404 if not found.",
)
def get_alert(alert_id: str) -> AlertResponse:
    """Return a single alert by ID."""
    alert = alert_service.get_alert_by_id(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert
