"""
Global Redis client singleton.
Connects to Redis on localhost:6379 with password auth.
"""

from __future__ import annotations

import redis.asyncio as aioredis

from app.config import settings

redis_client: aioredis.Redis | None = None


async def init_redis() -> aioredis.Redis:
    """Create and return the global Redis client."""
    global redis_client
    redis_client = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        max_connections=50,
    )
    # Verify connectivity
    await redis_client.ping()
    return redis_client


async def close_redis() -> None:
    """Gracefully close the Redis connection pool."""
    global redis_client
    if redis_client is not None:
        await redis_client.aclose()
        redis_client = None


def get_redis_client() -> aioredis.Redis:
    """Return the active Redis client. Raises if not initialized."""
    if redis_client is None:
        raise RuntimeError("Redis client has not been initialized.")
    return redis_client
