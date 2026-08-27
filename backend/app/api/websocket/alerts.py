"""
Dummy WebSocket endpoint for live alert simulation.

DUMMY BEHAVIOUR (per IROCHI_INIT_PROMPT.md Section 10):

  1. Client connects.
  2. Simulate a PostgreSQL-backed backfill by sending a small batch
     of existing mock alerts first.
  3. Send a "backfill_complete" marker.
  4. Enter live mode.
  5. Send a new mock alert periodically.
  6. The distinction between "backfill" and "live" is explicit in the
     message structure.

IMPORTANT:
  - This is ONLY a simulation.
  - PostgreSQL and Redis Pub/Sub are NOT implemented.
  - The real WebSocket protocol will be defined later.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import (
    WS_BACKFILL_COUNT,
    WS_LIVE_INTERVAL_SECONDS,
    WS_LIVE_MAX_ALERTS,
)
from app.schemas.alerts import WebSocketMessage
from app.services.alert_service import alert_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket) -> None:
    """Dummy WebSocket endpoint simulating backfill + live alert delivery."""

    await websocket.accept()
    logger.info("WebSocket client connected")

    try:
        # --- Phase 1: Simulated backfill ---
        backfill_alerts = alert_service.get_backfill_alerts(WS_BACKFILL_COUNT)
        for alert in backfill_alerts:
            msg = WebSocketMessage(type="backfill", alert=alert)
            await websocket.send_json(msg.model_dump(mode="json"))

        # Signal that backfill is complete
        complete_msg = WebSocketMessage(type="backfill_complete", alert=None)
        await websocket.send_json(complete_msg.model_dump(mode="json"))
        logger.info(
            "Backfill complete: sent %d alerts", len(backfill_alerts)
        )

        # --- Phase 2: Simulated live stream ---
        for i in range(WS_LIVE_MAX_ALERTS):
            await asyncio.sleep(WS_LIVE_INTERVAL_SECONDS)
            live_alert = alert_service.generate_live_alert(i)
            msg = WebSocketMessage(type="live", alert=live_alert)
            await websocket.send_json(msg.model_dump(mode="json"))
            logger.debug("Live alert sent: %s", live_alert.alert_id)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception:
        logger.exception("WebSocket error")
        await websocket.close(code=1011)
