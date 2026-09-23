"""
Redis Pub/Sub subscriber for real-time alert broadcasting.
Subscribes to alerts:live and alert_status_updates channels.
"""

from __future__ import annotations

import json

import redis.asyncio as aioredis
import structlog

from app.websocket.connection_manager import ConnectionManager

logger = structlog.get_logger(__name__)


async def subscribe_to_alerts(
    redis: aioredis.Redis,
    manager: ConnectionManager,
) -> None:
    """
    Subscribe to Redis Pub/Sub channels and broadcast to all
    connected WebSocket clients. Runs indefinitely as a background task.
    """
    pubsub = redis.pubsub()
    await pubsub.subscribe("alerts:live", "alert_status_updates")
    logger.info("redis_pubsub_subscribed", channels=["alerts:live", "alert_status_updates"])

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            try:
                data = json.loads(message["data"])
                channel = message["channel"]
                # Handle both bytes and str channel names
                if isinstance(channel, bytes):
                    channel = channel.decode()

                if channel == "alerts:live":
                    await manager.broadcast({
                        "type": "new_alert",
                        "payload": data,
                    })
                elif channel == "alert_status_updates":
                    await manager.broadcast({
                        "type": "alert_status_changed",
                        "payload": data,
                    })

                logger.debug("pubsub_broadcast", channel=channel)
            except (json.JSONDecodeError, TypeError) as exc:
                logger.warning("pubsub_parse_error", error=str(exc))
            except Exception as exc:
                logger.error("pubsub_broadcast_error", error=str(exc))
    except Exception as exc:
        logger.error("pubsub_subscriber_fatal", error=str(exc))
    finally:
        await pubsub.unsubscribe("alerts:live", "alert_status_updates")
        await pubsub.aclose()
        logger.info("redis_pubsub_unsubscribed")
