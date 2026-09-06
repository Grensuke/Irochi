from typing import AsyncGenerator
from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.postgres_alert_service import PostgresAlertService
from app.services.redis_pubsub import RedisPubSubService
from app.services.alert_engine import AlertEngine
from app.core.config import REDIS_URL

# Global Redis pubsub instance
_redis_pubsub: RedisPubSubService | None = None

async def get_redis_pubsub() -> RedisPubSubService:
    global _redis_pubsub
    if _redis_pubsub is None:
        _redis_pubsub = RedisPubSubService(redis_url=REDIS_URL)
        await _redis_pubsub.start()
    return _redis_pubsub

def get_postgres_alert_service(db: AsyncSession = Depends(get_db)) -> PostgresAlertService:
    return PostgresAlertService(db)

def get_alert_engine(
    postgres_service: PostgresAlertService = Depends(get_postgres_alert_service),
    redis_service: RedisPubSubService = Depends(get_redis_pubsub)
) -> AlertEngine:
    return AlertEngine(postgres_service, redis_service)
