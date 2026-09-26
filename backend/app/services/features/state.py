from typing import Any, Dict, List, Tuple
from app.services.state.redis_client import RedisStateService
from app.schemas.features import EntityType
from app.services.features.keys import (
    build_sliding_bucket_key,
    build_tumbling_distinct_key,
    build_tumbling_metric_key,
    build_tumbling_list_key,
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

    async def append_tumbling_list(
        self,
        entity_type: EntityType,
        entity_key: str,
        window_id: int,
        field: str,
        value: str,
        ttl_seconds: int,
        max_length: int = 1000
    ):
        """Appends a value to a bounded list for a tumbling window."""
        key = build_tumbling_list_key(entity_type, entity_key, window_id, field)
        if self.redis._client is None:
            raise RuntimeError("Redis client is not started")

        async with self.redis._client.pipeline(transaction=True) as pipe:
            pipe.rpush(key, value)
            pipe.ltrim(key, -max_length, -1)
            pipe.expire(key, ttl_seconds)
            await pipe.execute()

    async def get_tumbling_list(
        self,
        entity_type: EntityType,
        entity_key: str,
        window_id: int,
        field: str
    ) -> List[str]:
        """Gets all values in a bounded list for a tumbling window."""
        key = build_tumbling_list_key(entity_type, entity_key, window_id, field)
        if self.redis._client is None:
            raise RuntimeError("Redis client is not started")
        return await self.redis._client.lrange(key, 0, -1)

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

    async def execute_tumbling_batch(
        self,
        entity_type: EntityType,
        entity_key: str,
        window_id: int,
        increments: Dict[str, int],
        distinct_adds: Dict[str, str],
        list_appends: Dict[str, str],
        ttl_seconds: int,
        max_list_length: int = 1000
    ) -> Tuple[Dict[str, str], Dict[str, int], Dict[str, List[str]]]:
        """
        Executes writes and reads for a tumbling window in a single Redis pipeline roundtrip.
        """
        if self.redis._client is None:
            raise RuntimeError("Redis client is not started")

        metric_key = build_tumbling_metric_key(entity_type, entity_key, window_id)
        
        async with self.redis._client.pipeline(transaction=True) as pipe:
            # 1. Writes
            if increments:
                for field, amount in increments.items():
                    if amount != 0:
                        pipe.hincrby(metric_key, field, amount)
                pipe.expire(metric_key, ttl_seconds)
                
            for field, value in distinct_adds.items():
                if value is not None:
                    d_key = build_tumbling_distinct_key(entity_type, entity_key, window_id, field)
                    pipe.pfadd(d_key, value)
                    pipe.expire(d_key, ttl_seconds)
                    
            for field, value in list_appends.items():
                if value is not None:
                    l_key = build_tumbling_list_key(entity_type, entity_key, window_id, field)
                    pipe.rpush(l_key, value)
                    pipe.ltrim(l_key, -max_list_length, -1)
                    pipe.expire(l_key, ttl_seconds)
                    
            # 2. Reads
            pipe.hgetall(metric_key)
            distinct_keys = list(distinct_adds.keys())
            for field in distinct_keys:
                d_key = build_tumbling_distinct_key(entity_type, entity_key, window_id, field)
                pipe.pfcount(d_key)
                
            list_keys = list(list_appends.keys())
            for field in list_keys:
                l_key = build_tumbling_list_key(entity_type, entity_key, window_id, field)
                pipe.lrange(l_key, 0, -1)
                
            results = await pipe.execute()
            
        # 3. Parse results from the back of the results array
        total_reads = 1 + len(distinct_keys) + len(list_keys)
        read_results = results[-total_reads:] if total_reads > 0 else []
        
        metrics_raw = read_results[0] if read_results else {}
        metrics = {}
        if isinstance(metrics_raw, dict):
            for k, v in metrics_raw.items():
                k_str = k.decode('utf-8') if isinstance(k, bytes) else k
                v_str = v.decode('utf-8') if isinstance(v, bytes) else v
                metrics[k_str] = v_str
        
        distinct_counts = {}
        idx = 1
        for field in distinct_keys:
            distinct_counts[field] = read_results[idx]
            idx += 1
            
        list_values = {}
        for field in list_keys:
            list_values[field] = read_results[idx]
            idx += 1
            
        return metrics, distinct_counts, list_values
