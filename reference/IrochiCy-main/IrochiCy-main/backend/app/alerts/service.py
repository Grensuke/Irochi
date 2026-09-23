"""Alerts business logic with status transitions, audit logging, and Redis pub/sub."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID

import redis.asyncio as aioredis
import structlog
from fastapi import HTTPException, status
from sqlalchemy import Text, cast, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts.models import Alert, AlertStatusHistory, AuditLog
from app.alerts.schemas import (
    AlertFilters,
    AlertListResponse,
    AlertResponse,
    AlertStatusUpdate,
)

logger = structlog.get_logger(__name__)

# ── Status transition table ──────────────────────────────────────

VALID_TRANSITIONS: dict[str, set[str]] = {
    "new": {"acknowledged", "investigating", "escalated", "closed"},
    "acknowledged": {"investigating", "escalated", "closed"},
    "investigating": {"escalated", "closed"},
    "escalated": {"closed"},
    "closed": set(),  # terminal state
}


async def list_alerts(
    db: AsyncSession,
    filters: AlertFilters,
) -> AlertListResponse:
    """List alerts with dynamic filtering, IP partial match, and pagination."""

    query = select(Alert)
    count_query = select(func.count()).select_from(Alert)

    # Apply non-None filters
    if filters.threat_type:
        query = query.where(Alert.threat_type == filters.threat_type)
        count_query = count_query.where(Alert.threat_type == filters.threat_type)
    if filters.severity:
        query = query.where(Alert.severity == filters.severity)
        count_query = count_query.where(Alert.severity == filters.severity)
    if filters.status:
        query = query.where(Alert.status == filters.status)
        count_query = count_query.where(Alert.status == filters.status)

    # IP partial match using ILIKE on cast to text
    if filters.src_ip:
        query = query.where(
            cast(Alert.src_ip, Text).ilike(f"%{filters.src_ip}%")
        )
        count_query = count_query.where(
            cast(Alert.src_ip, Text).ilike(f"%{filters.src_ip}%")
        )
    if filters.dst_ip:
        query = query.where(
            cast(Alert.dst_ip, Text).ilike(f"%{filters.dst_ip}%")
        )
        count_query = count_query.where(
            cast(Alert.dst_ip, Text).ilike(f"%{filters.dst_ip}%")
        )

    # Free-text search across both IP columns
    if filters.search:
        search_term = f"%{filters.search}%"
        ip_filter = (
            cast(Alert.src_ip, Text).ilike(search_term)
            | cast(Alert.dst_ip, Text).ilike(search_term)
        )
        query = query.where(ip_filter)
        count_query = count_query.where(ip_filter)

    # Cursor-based: alerts after a specific timestamp (for WS backfill)
    if filters.after:
        query = query.where(Alert.created_at > filters.after)
        count_query = count_query.where(Alert.created_at > filters.after)

    # Total count
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Order and paginate
    query = query.order_by(Alert.created_at.desc())
    offset = (filters.page - 1) * filters.page_size
    query = query.offset(offset).limit(filters.page_size)

    result = await db.execute(query)
    alerts = list(result.scalars().all())

    return AlertListResponse(
        items=[AlertResponse.model_validate(a) for a in alerts],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        has_next=(offset + filters.page_size) < total,
    )


async def get_alert(db: AsyncSession, alert_id: UUID) -> AlertResponse | None:
    """Retrieve a single alert by ID."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if alert is None:
        return None
    return AlertResponse.model_validate(alert)


async def update_alert_status(
    db: AsyncSession,
    redis: aioredis.Redis,
    alert_id: UUID,
    update_req: AlertStatusUpdate,
    changed_by_id: UUID,
    changed_by_username: str,
) -> AlertResponse:
    """
    Update alert status with strict transition enforcement.
    Inserts history, audit log, and publishes to Redis.
    """
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    current_status = alert.status
    new_status = update_req.status

    # Enforce transition table
    allowed = VALID_TRANSITIONS.get(current_status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Invalid status transition: '{current_status}' → '{new_status}'. "
                f"Allowed transitions: {sorted(allowed) if allowed else 'none (terminal state)'}"
            ),
        )

    # Update alert
    alert.status = new_status

    # Append note with timestamp prefix
    if update_req.note:
        timestamp_prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        note_entry = f"[{timestamp_prefix}] [{changed_by_username}] {update_req.note}"
        if alert.analyst_notes:
            alert.analyst_notes = f"{alert.analyst_notes}\n{note_entry}"
        else:
            alert.analyst_notes = note_entry

    # Insert status history
    history = AlertStatusHistory(
        alert_id=alert.id,
        old_status=current_status,
        new_status=new_status,
        changed_by=changed_by_id,
        note=update_req.note,
    )
    db.add(history)

    # Insert audit log
    audit = AuditLog(
        user_id=changed_by_id,
        action="alert_status_update",
        resource_type="alert",
        resource_id=alert.id,
        payload={
            "old_status": current_status,
            "new_status": new_status,
            "note": update_req.note,
        },
    )
    db.add(audit)

    await db.commit()
    await db.refresh(alert)

    # Publish to Redis for WebSocket broadcast
    try:
        await redis.publish(
            "alert_status_updates",
            json.dumps({
                "alert_id": str(alert.id),
                "new_status": new_status,
                "old_status": current_status,
                "changed_by": changed_by_username,
            }),
        )
    except Exception as exc:
        logger.warning("redis_publish_failed", channel="alert_status_updates", error=str(exc))

    logger.info(
        "alert_status_updated",
        alert_id=str(alert_id),
        transition=f"{current_status} → {new_status}",
        changed_by=changed_by_username,
    )

    return AlertResponse.model_validate(alert)
