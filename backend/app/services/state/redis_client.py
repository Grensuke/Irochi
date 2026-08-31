import logging
from typing import Any

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RedisStateService:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client: Redis | None = None

    async def start(self):
        """Start the Redis connection pool."""
        if self._client is None:
            self._client = Redis.from_url(self.redis_url, decode_responses=True)
            await self._client.ping()
            logger.info("Redis State Service started.")

    async def stop(self):
        """Stop the Redis connection pool."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("Redis State Service stopped.")

    async def increment_hash_fields(self, key: str, increments: dict[str, int]):
        """
        Increment multiple fields in a hash atomically.
        Used for sliding window counters and Tier 1 gating state.

        Note: TTLs are not managed here; they remain an OPEN Feature/Window implementation detail.
        """
        if self._client is None:
            raise RuntimeError("Redis client is not started")

        async with self._client.pipeline(transaction=True) as pipe:
            for field, amount in increments.items():
                pipe.hincrby(key, field, amount)
            await pipe.execute()

    async def set_correlation(self, key: str, fields: dict[str, Any], ttl_seconds: int | None = None):
        """
        Set multiple fields in a short-lived correlation hash.
        """
        if self._client is None:
            raise RuntimeError("Redis client is not started")

        async with self._client.pipeline(transaction=True) as pipe:
            pipe.hset(key, mapping=fields)
            if ttl_seconds is not None:
                pipe.expire(key, ttl_seconds)
            await pipe.execute()

    async def get_correlation(self, key: str) -> dict[str, str]:
        """
        Get all fields from a correlation hash.
        """
        if self._client is None:
            raise RuntimeError("Redis client is not started")

        return await self._client.hgetall(key)

    async def add_distinct(self, key: str, value: str):
        """
        Add a value to a distinct-count structure (HyperLogLog).
        Used for Tumbling breadth features (e.g., unique destination ports/hosts).
        """
        if self._client is None:
            raise RuntimeError("Redis client is not started")

        await self._client.pfadd(key, value)
