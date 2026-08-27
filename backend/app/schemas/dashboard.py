"""Dashboard summary schemas."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.alerts import AlertResponse


class DashboardSummaryResponse(BaseModel):
    """Response model for the dashboard summary endpoint."""

    total_alerts: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    by_threat_type: dict[str, int]
    by_detector: dict[str, int]
    recent_alerts: list[AlertResponse]
