"""Dashboard routes — summary endpoint."""

from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends

from app.schemas.dashboard import DashboardSummaryResponse
from app.services.postgres_alert_service import PostgresAlertService
from app.api.dependencies import get_postgres_alert_service

router = APIRouter()


@router.get(
    "/dashboard/summary",
    response_model=DashboardSummaryResponse,
    summary="Dashboard summary",
    description="Return aggregate dashboard metrics computed from PostgreSQL alerts.",
)
async def dashboard_summary(
    alert_service: Annotated[PostgresAlertService, Depends(get_postgres_alert_service)]
) -> DashboardSummaryResponse:
    """Return dashboard summary metrics."""
    return await alert_service.get_dashboard_summary()
