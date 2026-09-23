"""Dashboard API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard import service
from app.dashboard.schemas import (
    DashboardSummary,
    KPIData,
    TimelineResponse,
    TopSourceIP,
    TopThreat,
)
from app.dependencies import get_current_user, get_db, get_redis
from app.users.models import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_summary(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    _current_user: User = Depends(get_current_user),
) -> DashboardSummary:
    """Full dashboard summary (5-second Redis cache)."""
    return await service.get_dashboard_summary(db, redis)


@router.get("/kpi", response_model=KPIData)
async def get_kpi(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    _current_user: User = Depends(get_current_user),
) -> KPIData:
    """Live KPI metrics."""
    return await service.get_kpi(db, redis)


@router.get("/timeline", response_model=TimelineResponse)
async def get_timeline(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> TimelineResponse:
    """24-hour alert timeline bucketed by threat type."""
    return await service.get_timeline(db)


@router.get("/top-threats", response_model=list[TopThreat])
async def get_top_threats(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[TopThreat]:
    """Top threat types today with percentages."""
    return await service.get_top_threats(db)


@router.get("/top-ips", response_model=list[TopSourceIP])
async def get_top_ips(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[TopSourceIP]:
    """Top 10 source IPs today."""
    return await service.get_top_source_ips(db)
