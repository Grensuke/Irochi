"""WebSocket API route for real-time alert streaming with JWT auth and backfill."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts.schemas import AlertFilters
from app.alerts.service import list_alerts
from app.auth.utils import decode_token
from app.dependencies import get_db, get_redis
from app.users.models import User
from app.websocket.connection_manager import manager

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/alerts")
async def websocket_alerts(
    websocket: WebSocket,
    token: str = Query(...),
    last_cursor: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> None:
    """
    WebSocket endpoint for real-time alert streaming.

    Authentication via query parameter `token` (JWT) since WebSocket
    cannot use Authorization headers.

    Optional `last_cursor` (ISO datetime) to backfill missed alerts
    since the client's last known timestamp.
    """

    # Validate JWT from query param
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("Only access tokens are allowed")
            
        username = payload.get("sub")
        if not username:
            raise ValueError("Missing subject in token")

        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise ValueError("Invalid or inactive user")
    except Exception:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    # Connect
    await manager.connect(str(user.id), websocket)

    try:
        # Backfill missed alerts if cursor provided
        if last_cursor:
            try:
                cursor_dt = datetime.fromisoformat(last_cursor)
                missed = await list_alerts(
                    db,
                    AlertFilters(after=cursor_dt, page_size=100),
                )
                for alert in missed.items:
                    await websocket.send_json({
                        "type": "backfill",
                        "payload": alert.model_dump(mode="json"),
                    })
                await websocket.send_json({"type": "backfill_complete"})
            except Exception as exc:
                logger.warning("ws_backfill_error", error=str(exc))

        # Notify client of successful connection
        await websocket.send_json({
            "type": "connected",
            "payload": {
                "user_id": str(user.id),
                "username": user.username,
                "connection_count": manager.connection_count,
                "server_time": datetime.utcnow().isoformat(),
            },
        })

        # Keep-alive loop — wait for client messages
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        manager.disconnect(str(user.id), websocket)
        logger.info("ws_client_disconnected", user_id=str(user.id))
    except Exception as exc:
        manager.disconnect(str(user.id), websocket)
        logger.error("ws_unexpected_error", user_id=str(user.id), error=str(exc))
