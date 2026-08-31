from typing import Any, Dict, List
from app.services.state.redis_client import RedisStateService
from app.schemas.features import EntityType

class FeatureStateAdapter:
    """Adapts the raw RedisStateService for Feature/Window specific state."""

    def __init__(self, redis_service: RedisStateService):
        self.redis = redis_service

    async def get_revision(self, entity_type: EntityType, entity_key: str) -> int:
        """
        Gets a new monotonically increasing revision for a snapshot.
        The exact revision/staleness/idempotency mechanism remains OPEN.
        This is a local development implementation using Redis INCR.
        """
        key = f"irochi:revision:{entity_type.value}:{entity_key}"
        if self.redis._client is None:
            raise RuntimeError("Redis client is not started")
        return await self.redis._client.incr(key)

    async def increment_sliding_bucket(
        self,
        entity_type: EntityType,
        entity_key: str,
        time_bucket: int,
        increments: Dict[str, int],
        ttl_seconds: int
    ):
        """
        Increments a sliding window bucket and sets its TTL.
        The exact TTL durations remain OPEN and must be supplied by configuration.
        """
        key = f"irochi:feature:{entity_type.value}:{entity_key}:bucket:{time_bucket}"
        if self.redis._client is None:
            raise RuntimeError("Redis client is not started")

        async with self.redis._client.pipeline(transaction=True) as pipe:
            for field, amount in increments.items():
                pipe.hincrby(key, field, amount)
            pipe.expire(key, ttl_seconds)
            await pipe.execute()

    async def get_sliding_buckets(
        self,
        entity_type: EntityType,
        entity_key: str,
        active_buckets: List[int]
    ) -> List[Dict[str, str]]:
        """Gets all fields for a set of active time buckets."""
        if self.redis._client is None:
            raise RuntimeError("Redis client is not started")

        async with self.redis._client.pipeline(transaction=False) as pipe:
            for bucket in active_buckets:
                key = f"irochi:feature:{entity_type.value}:{entity_key}:bucket:{bucket}"
                pipe.hgetall(key)
            results = await pipe.execute()
        return results

    async def add_tumbling_distinct(
        self,
        entity_type: EntityType,
        entity_key: str,
        window_id: int,
        field: str,
        value: str,
        ttl_seconds: int
    ):
        """
        Adds a distinct value for a tumbling window (using HLL) and sets TTL.
        The exact TTL durations remain OPEN and must be supplied by configuration.
        """
        key = f"irochi:feature:{entity_type.value}:{entity_key}:hll:{window_id}:{field}"
        if self.redis._client is None:
            raise RuntimeError("Redis client is not started")

        async with self.redis._client.pipeline(transaction=True) as pipe:
            pipe.pfadd(key, value)
            pipe.expire(key, ttl_seconds)
            await pipe.execute()

    async def count_tumbling_distinct(
        self,
        entity_type: EntityType,
        entity_key: str,
        window_id: int,
        field: str
    ) -> int:
        """Gets the distinct count for a tumbling window."""
        key = f"irochi:feature:{entity_type.value}:{entity_key}:hll:{window_id}:{field}"
        if self.redis._client is None:
            raise RuntimeError("Redis client is not started")
        return await self.redis._client.pfcount(key)

    async def set_correlation_state(
        self,
        connection_id: str,
        fields: Dict[str, Any],
        ttl_seconds: int
    ):
        key = f"irochi:feature:connection:{connection_id}:correlation"
        await self.redis.set_correlation(key, fields, ttl_seconds)

    async def get_correlation_state(self, connection_id: str) -> Dict[str, str]:
        key = f"irochi:feature:connection:{connection_id}:correlation"
        return await self.redis.get_correlation(key)
