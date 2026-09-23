"""Alerts API routes with CSV streaming export."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts import service
from app.alerts.models import Alert
from app.alerts.schemas import (
    AlertFilters,
    AlertListResponse,
    AlertResponse,
    AlertStatusUpdate,
)
from app.dependencies import get_current_user, get_db, get_redis
from app.users.models import User

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=AlertListResponse)
async def list_alerts(
    threat_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    src_ip: Optional[str] = Query(None),
    dst_ip: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    after: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> AlertListResponse:
    """List alerts with filtering and pagination."""
    filters = AlertFilters(
        threat_type=threat_type,
        severity=severity,
        status=status,
        src_ip=src_ip,
        dst_ip=dst_ip,
        search=search,
        after=after,
        page=page,
        page_size=page_size,
    )
    return await service.list_alerts(db, filters)


@router.get("/export/csv")
async def export_alerts_csv(
    threat_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Export alerts as a streaming CSV download."""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    filename = f"sih26145_alerts_{today}.csv"

    async def generate_csv() -> AsyncGenerator[str, None]:
        # Header row
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "threat_type", "severity", "confidence",
            "src_ip", "dst_ip", "src_port", "dst_port",
            "protocol", "status", "created_at",
        ])
        yield output.getvalue()

        # Stream rows in chunks of 500
        offset = 0
        chunk_size = 500
        while True:
            query = select(Alert).order_by(Alert.created_at.desc())
            if threat_type:
                query = query.where(Alert.threat_type == threat_type)
            if severity:
                query = query.where(Alert.severity == severity)
            if status:
                query = query.where(Alert.status == status)
            query = query.offset(offset).limit(chunk_size)

            result = await db.execute(query)
            alerts = result.scalars().all()

            if not alerts:
                break

            output = io.StringIO()
            writer = csv.writer(output)
            for alert in alerts:
                writer.writerow([
                    str(alert.id),
                    alert.threat_type,
                    alert.severity,
                    alert.confidence,
                    str(alert.src_ip),
                    str(alert.dst_ip),
                    alert.src_port,
                    alert.dst_port,
                    alert.protocol,
                    alert.status,
                    alert.created_at.isoformat(),
                ])
            yield output.getvalue()
            offset += chunk_size

    return StreamingResponse(
        generate_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> AlertResponse:
    """Retrieve a single alert by ID."""
    alert = await service.get_alert(db, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.patch("/{alert_id}/status", response_model=AlertResponse)
async def update_alert_status(
    alert_id: UUID,
    body: AlertStatusUpdate,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    current_user: User = Depends(get_current_user),
) -> AlertResponse:
    """Update alert status with strict transition enforcement."""
    return await service.update_alert_status(
        db=db,
        redis=redis,
        alert_id=alert_id,
        update_req=body,
        changed_by_id=current_user.id,
        changed_by_username=current_user.username,
    )
