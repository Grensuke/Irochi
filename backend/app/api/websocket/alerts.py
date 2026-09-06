"""
WebSocket endpoint for live alert streaming.

Supports backfill via PostgreSQL and live stream via Redis Pub/Sub.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from app.core.config import WS_BACKFILL_COUNT
from app.schemas.alerts import WebSocketMessage, AlertResponse
from app.services.postgres_alert_service import PostgresAlertService
from app.services.redis_pubsub import RedisPubSubService
from app.api.dependencies import get_postgres_alert_service, get_redis_pubsub

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/alerts")
async def websocket_alerts(
    websocket: WebSocket,
    alert_service: Annotated[PostgresAlertService, Depends(get_postgres_alert_service)],
    pubsub_service: Annotated[RedisPubSubService, Depends(get_redis_pubsub)],
) -> None:
    """WebSocket endpoint pushing backfill + live alerts."""

    await websocket.accept()
    logger.info("WebSocket client connected")

    try:
        # --- Phase 1: Real Postgres backfill ---
        backfill_alerts_orm = await alert_service.list_alerts(limit=WS_BACKFILL_COUNT)

        # We need to reverse them so the oldest of the backfill comes first
        for a in reversed(backfill_alerts_orm):
            alert = AlertResponse(
                alert_id=str(a.alert_id),
                timestamp=a.last_seen_at,
                threat_type=a.threat_type,
                detector_id=a.detector_id,
                severity=a.severity,
                confidence=a.confidence or 0.0,
                entity_type=a.entity_type,
                entity_key=a.entity_key,
                first_seen_at=a.first_seen_at,
                last_seen_at=a.last_seen_at,
                resolved_at=a.resolved_at,
                evidence_summary=a.evidence_summary or "",
                status=a.status
            )
            msg = WebSocketMessage(type="backfill", alert=alert)
            await websocket.send_json(msg.model_dump(mode="json"))

        # Signal that backfill is complete
        complete_msg = WebSocketMessage(type="backfill_complete", alert=None)
        await websocket.send_json(complete_msg.model_dump(mode="json"))
        logger.info("Backfill complete: sent %d alerts", len(backfill_alerts_orm))

        # --- Phase 2: Real Redis live stream ---
        async for live_payload in pubsub_service.subscribe_alerts():
            # Validate through the AlertResponse schema
            live_alert = AlertResponse(**live_payload["alert"])
            msg = WebSocketMessage(type="live", alert=live_alert)
            await websocket.send_json(msg.model_dump(mode="json"))
            logger.debug("Live alert sent: %s", live_alert.alert_id)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception:
        logger.exception("WebSocket error")
        await websocket.close(code=1011)
