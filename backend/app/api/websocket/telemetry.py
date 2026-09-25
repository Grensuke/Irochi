import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from app.api.dependencies import get_redis_pubsub
from app.services.redis_pubsub import RedisPubSubService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/telemetry")
async def websocket_telemetry(
    websocket: WebSocket,
    redis_service: RedisPubSubService = Depends(get_redis_pubsub),
):
    """WebSocket endpoint pushing live telemetry stats and samples."""
    await websocket.accept()
    logger.info("WebSocket telemetry client connected")

    try:
        async for stats in redis_service.subscribe_telemetry():
            await websocket.send_json(stats)
    except WebSocketDisconnect:
        logger.info("WebSocket telemetry client disconnected")
    except Exception as e:
        logger.exception("WebSocket telemetry error")
        try:
            await websocket.close(code=1011)
        except RuntimeError:
            pass
