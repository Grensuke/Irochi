"""Threat intelligence API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, get_redis
from app.threats import service
from app.threats.schemas import ThreatDetailResponse, ThreatTypeStat
from app.users.models import User

router = APIRouter(prefix="/threats", tags=["threats"])


@router.get("/", response_model=list[ThreatTypeStat])
async def list_threat_types(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    _current_user: User = Depends(get_current_user),
) -> list[ThreatTypeStat]:
    """List all 5 threat type stats with live DB counts and detector status."""
    return await service.get_threat_types(db, redis)


@router.get("/{threat_type}", response_model=ThreatDetailResponse)
async def get_threat_detail(
    threat_type: str,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    _current_user: User = Depends(get_current_user),
) -> ThreatDetailResponse:
    """Detailed view for a single threat type with confidence distribution."""
    return await service.get_threat_detail(db, redis, threat_type)
