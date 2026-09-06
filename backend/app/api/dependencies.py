import logging
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import config
from app.core.database import get_db
from app.services.postgres_alert_service import PostgresAlertService
from app.services.redis_pubsub import RedisPubSubService
from app.services.alert_engine import AlertEngine

logger = logging.getLogger(__name__)

# Singleton instance of Redis PubSub service
_redis_pubsub_service: RedisPubSubService | None = None

async def get_redis_pubsub() -> RedisPubSubService:
    global _redis_pubsub_service
    if _redis_pubsub_service is None:
        _redis_pubsub_service = RedisPubSubService(config.REDIS_URL)
        await _redis_pubsub_service.start()
    return _redis_pubsub_service

async def get_postgres_alert_service(
    db: AsyncSession = Depends(get_db)
) -> PostgresAlertService:
    """Dependency to provide PostgresAlertService for API routes."""
    return PostgresAlertService(db)

async def get_alert_engine(
    db_service: PostgresAlertService = Depends(get_postgres_alert_service),
    pubsub_service: RedisPubSubService = Depends(get_redis_pubsub)
) -> AlertEngine:
    return AlertEngine(db_service, pubsub_service)
