from app.services.state.redis_client import RedisStateService

class BaselineStateStore:
    def __init__(self, redis_service: RedisStateService):
        self.redis = redis_service

    async def get_stats(self, detector_domain: str, entity_type: str, entity_key: str, signal_name: str) -> dict[str, float]:
        """
        Retrieves the Welford baseline statistics for a specific signal.
        Returns a dictionary with 'count', 'mean', and 'm2' as floats.
        """
        key = f"vibhinetra:anomaly:baseline:{detector_domain}:{entity_type}:{entity_key}:{signal_name}"
        data = await self.redis.get_state_hash(key)
        
        if not data:
            return {"count": 0.0, "mean": 0.0, "m2": 0.0}
            
        return {
            "count": float(data.get("count", 0.0)),
            "mean": float(data.get("mean", 0.0)),
            "m2": float(data.get("m2", 0.0))
        }

    async def update_stats(self, detector_domain: str, entity_type: str, entity_key: str, signal_name: str, value: float):
        """
        Updates the Welford baseline statistics for a specific signal.
        No TTL is set, as this is long-lived state.
        """
        key = f"vibhinetra:anomaly:baseline:{detector_domain}:{entity_type}:{entity_key}:{signal_name}"
        stats = await self.get_stats(detector_domain, entity_type, entity_key, signal_name)
        
        count = stats["count"]
        mean = stats["mean"]
        m2 = stats["m2"]
        
        count += 1.0
        delta = value - mean
        mean += delta / count
        delta2 = value - mean
        m2 += delta * delta2
        
        await self.redis.set_state_hash(key, {
            "count": str(count),
            "mean": str(mean),
            "m2": str(m2)
        })
