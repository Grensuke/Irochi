import json
import logging
from typing import AsyncGenerator

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RedisPubSubService:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client: Redis | None = None
        self._channel = "irochi.alerts.live"

    async def start(self):
        if self._client is None:
            self._client = Redis.from_url(self.redis_url, decode_responses=True)
            logger.info("Redis PubSub Service started.")

    async def stop(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("Redis PubSub Service stopped.")

    async def publish_alert(self, alert_payload: dict):
        """
        Publish an alert to the live Redis channel.
        """
        if self._client is None:
            raise RuntimeError("Redis PubSub client is not started")

        message = json.dumps(alert_payload)
        await self._client.publish(self._channel, message)

    async def subscribe_alerts(self) -> AsyncGenerator[dict, None]:
        """
        Subscribe to the live alert channel and yield messages.
        """
        if self._client is None:
            raise RuntimeError("Redis PubSub client is not started")

        pubsub = self._client.pubsub()
        await pubsub.subscribe(self._channel)

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        yield data
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse pub/sub message: {e}")
        finally:
            await pubsub.unsubscribe(self._channel)
            await pubsub.close()
