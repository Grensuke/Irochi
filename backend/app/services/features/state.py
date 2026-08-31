from typing import Any, Dict, List
from app.services.state.redis_client import RedisStateService
from app.schemas.features import EntityType
from app.services.features.keys import (
    build_sliding_bucket_key,
    build_tumbling_distinct_key,
    build_tumbling_metric_key,
    build_correlation_key,
    build_revision_key
)

class RevisionGenerator:
    """
    Isolates revision generation for feature records.
    Monotonicity is required as an invariant.
    The exact revision storage/generation mechanism remains OPEN.
    The current Redis INCR mechanism is a replaceable development baseline.
    """
    def __init__(self, redis_service: RedisStateService):
        self.redis = redis_service

    async def get_next_revision(self, entity_type: EntityType, entity_key: str) -> int:
        key = build_revision_key(entity_type, entity_key)
        if self.redis._client is None:
            raise RuntimeError("Redis client is not started")
        return await self.redis._client.incr(key)

class FeatureStateAdapter:
    """Adapts the raw RedisStateService for Feature/Window specific state."""

    def __init__(self, redis_service: RedisStateService):
        self.redis = redis_service
        self.revision_generator = RevisionGenerator(redis_service)

    async def get_revision(self, entity_type: EntityType, entity_key: str) -> int:
        """Delegates to the isolated RevisionGenerator."""
        return await self.revision_generator.get_next_revision(entity_type, entity_key)

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
        key = build_sliding_bucket_key(entity_type, entity_key, time_bucket)
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
                key = build_sliding_bucket_key(entity_type, entity_key, bucket)
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
        key = build_tumbling_distinct_key(entity_type, entity_key, window_id, field)
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
        key = build_tumbling_distinct_key(entity_type, entity_key, window_id, field)
        if self.redis._client is None:
            raise RuntimeError("Redis client is not started")
        return await self.redis._client.pfcount(key)

    async def increment_tumbling_metric(
        self,
        entity_type: EntityType,
        entity_key: str,
        window_id: int,
        increments: Dict[str, int],
        ttl_seconds: int
    ):
        """
        Increments numeric metrics in a tumbling window Hash and sets TTL.
        """
        key = build_tumbling_metric_key(entity_type, entity_key, window_id)
        if self.redis._client is None:
            raise RuntimeError("Redis client is not started")

        async with self.redis._client.pipeline(transaction=True) as pipe:
            for field, amount in increments.items():
                if amount != 0:
                    pipe.hincrby(key, field, amount)
            pipe.expire(key, ttl_seconds)
            await pipe.execute()

    async def get_tumbling_metrics(
        self,
        entity_type: EntityType,
        entity_key: str,
        window_id: int
    ) -> Dict[str, str]:
        """Gets all metrics for a tumbling window."""
        key = build_tumbling_metric_key(entity_type, entity_key, window_id)
        if self.redis._client is None:
            raise RuntimeError("Redis client is not started")
        return await self.redis._client.hgetall(key)

    async def set_correlation_state(
        self,
        connection_id: str,
        fields: Dict[str, Any],
        ttl_seconds: int
    ):
        key = build_correlation_key(connection_id)
        await self.redis.set_correlation(key, fields, ttl_seconds)

    async def get_correlation_state(self, connection_id: str) -> Dict[str, str]:
        key = build_correlation_key(connection_id)
        return await self.redis.get_correlation(key)
