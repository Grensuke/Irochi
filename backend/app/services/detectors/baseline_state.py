from app.services.state.redis_client import RedisStateService

class BaselineStateStore:
    def __init__(self, redis_service: RedisStateService):
        self.redis = redis_service

    async def bulk_get_stats(self, detector_domain: str, entity_type: str, entity_key: str, fields: list[str]) -> dict[str, dict[str, float]]:
        """Bulk retrieves Welford stats for multiple fields using a single Redis pipeline."""
        if not fields:
            return {}
            
        keys = [f"vibhinetra:anomaly:baseline:{detector_domain}:{entity_type}:{entity_key}:{k}" for k in fields]
        
        async with self.redis.redis.pipeline() as pipe:
            for key in keys:
                pipe.hgetall(key)
            results = await pipe.execute()
            
        final_stats = {}
        for i, field in enumerate(fields):
            data = results[i] or {}
            final_stats[field] = {
                "count": float(data.get(b"count", data.get("count", 0.0))),
                "mean": float(data.get(b"mean", data.get("mean", 0.0))),
                "m2": float(data.get(b"m2", data.get("m2", 0.0)))
            }
        return final_stats

    async def bulk_update_stats(self, detector_domain: str, entity_type: str, entity_key: str, fields: dict[str, float]):
        """Bulk updates Welford stats for multiple fields using a single Redis pipeline."""
        if not fields:
            return
            
        keys = [f"vibhinetra:anomaly:baseline:{detector_domain}:{entity_type}:{entity_key}:{k}" for k in fields.keys()]
        
        # 1. Pipeline GET all current stats
        async with self.redis.redis.pipeline() as pipe:
            for key in keys:
                pipe.hgetall(key)
            results = await pipe.execute()
            
        # 2. Pipeline SET all new stats
        async with self.redis.redis.pipeline() as pipe:
            for i, (field_name, value) in enumerate(fields.items()):
                key = keys[i]
                data = results[i] or {}
                
                count = float(data.get(b"count", data.get("count", 0.0)))
                mean = float(data.get(b"mean", data.get("mean", 0.0)))
                m2 = float(data.get(b"m2", data.get("m2", 0.0)))
                
                count += 1.0
                delta = value - mean
                mean += delta / count
                delta2 = value - mean
                m2 += delta * delta2
                
                # hgetall might return bytes in aioredis, so set standard strings
                pipe.hset(key, mapping={
                    "count": str(count),
                    "mean": str(mean),
                    "m2": str(m2)
                })
            await pipe.execute()
