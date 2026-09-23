"""Redis hot state writer for shared cross-worker state.

Read by FastAPI /dashboard/kpi endpoints.
"""

from __future__ import annotations

import time
from uuid import uuid4

import structlog

logger = structlog.get_logger(__name__)


class RedisHotState:
    """Writes shared pipeline state to Redis for dashboard consumption."""

    def __init__(self, redis_client) -> None:
        self._redis = redis_client

    async def increment_events_per_second(self, event_type: str) -> None:
        """Track events per second using a Redis sorted set.

        Uses sliding 1-second window via ZREMRANGEBYSCORE.
        """
        now = time.time()
        key = f"pipeline:eps:{event_type}"
        member = f"{now}:{uuid4().hex[:8]}"

        await self._redis.zadd(key, {member: now})
        await self._redis.zremrangebyscore(key, 0, now - 1.0)
        count = await self._redis.zcard(key)
        await self._redis.set("pipeline:events_per_second", str(count), ex=5)

    async def set_detector_status(self, threat_type: str, status: str) -> None:
        """Set detector status with 60s TTL.

        Worker must refresh or dashboard shows 'idle'.
        """
        key = f"pipeline:detector:{threat_type}:status"
        await self._redis.set(key, status, ex=60)

    async def record_detection_latency(self, latency_ms: int) -> None:
        """Record detection latency sample and compute p95."""
        key = "pipeline:latency_samples"
        await self._redis.lpush(key, str(latency_ms))
        await self._redis.ltrim(key, 0, 999)  # keep last 1000 samples

        # Compute p95
        raw_samples = await self._redis.lrange(key, 0, -1)
        if raw_samples:
            samples = sorted(int(s) for s in raw_samples)
            p95_idx = int(len(samples) * 0.95)
            p95 = samples[min(p95_idx, len(samples) - 1)]
            await self._redis.set("pipeline:latency_p95_ms", str(p95), ex=30)

    async def set_detectors_active(self, count: int) -> None:
        """Set the number of active detectors."""
        await self._redis.set("pipeline:detectors_active", str(count), ex=60)
