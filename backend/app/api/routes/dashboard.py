"""Dashboard routes — summary endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard_service import dashboard_service

router = APIRouter()


@router.get(
    "/dashboard/summary",
    response_model=DashboardSummaryResponse,
    summary="Dashboard summary",
    description="Return aggregate dashboard metrics computed from mock alerts.",
)
def dashboard_summary() -> DashboardSummaryResponse:
    """Return dashboard summary metrics."""
    return dashboard_service.get_summary()
