"""
Irochi backend — FastAPI application entry point.

DUMMY PHASE: Serves mock data through REST and WebSocket endpoints.
No real infrastructure (PostgreSQL, Redis, Redpanda) is connected.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import alerts as alert_routes
from app.api.routes import dashboard as dashboard_routes
from app.api.routes import health as health_routes
from app.api.websocket import alerts as ws_alerts
from contextlib import asynccontextmanager

from app.core.config import (
    API_V1_PREFIX, APP_DESCRIPTION, APP_TITLE, APP_VERSION,
    REDIS_URL, REDPANDA_BROKER, REDPANDA_CONSUMER_GROUP, REDPANDA_TOPICS
)
from app.core.database import AsyncSessionLocal
from app.services.state.redis_client import RedisStateService
from app.services.features.state import FeatureStateAdapter
from app.services.streaming.consumer import KafkaConsumerService
from app.services.features.engine import FeatureEngine
from app.services.detectors.registry import DetectorRegistry
from app.services.detectors.ddos import DdosDetector
from app.services.detectors.recon import ReconDetector
from app.services.detectors.dns import DnsDetector
from app.services.detectors.grouping import PassThroughGrouping
from app.services.detectors.router import DetectorRouter
from app.api.dependencies import get_redis_pubsub
from app.services.pipeline import DetectionPipeline

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)

# Global reference to pipeline to stop it on shutdown
_pipeline: DetectionPipeline | None = None
_state_service: RedisStateService | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pipeline, _state_service

    # 1. State/Infrastructure
    _state_service = RedisStateService(REDIS_URL)
    consumer = None
    try:
        await _state_service.start()
        state_adapter = FeatureStateAdapter(_state_service)

        redis_pubsub = await get_redis_pubsub()

        # 2. Streaming Consumer
        consumer = KafkaConsumerService(
            bootstrap_servers=REDPANDA_BROKER,
            group_id=REDPANDA_CONSUMER_GROUP,
            topics=REDPANDA_TOPICS,
        )
        await consumer.start()

        # 3. Engines & Router
        feature_engine = FeatureEngine(state_adapter)

        registry = DetectorRegistry()
        registry.register(DdosDetector())
        registry.register(ReconDetector())
        registry.register(DnsDetector())

        grouping = PassThroughGrouping()
        router = DetectorRouter(registry, grouping)

        # 4. Start Pipeline
        _pipeline = DetectionPipeline(
            consumer=consumer,
            feature_engine=feature_engine,
            router=router,
            session_factory=AsyncSessionLocal,
            redis_service=redis_pubsub,
        )
        _pipeline.start()

        yield
    finally:
        # Shutdown
        if _pipeline:
            await _pipeline.stop()
        if consumer:
            await consumer.stop()
        if _state_service:
            await _state_service.stop()


# ------------------------------------------------------------------
# Application
# ------------------------------------------------------------------

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
)

# ------------------------------------------------------------------
# CORS — permissive for dummy phase
# ------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# REST routes — all under /api/v1
# ------------------------------------------------------------------

app.include_router(health_routes.router, prefix=API_V1_PREFIX, tags=["health"])
app.include_router(alert_routes.router, prefix=API_V1_PREFIX, tags=["alerts"])
app.include_router(dashboard_routes.router, prefix=API_V1_PREFIX, tags=["dashboard"])

# ------------------------------------------------------------------
# WebSocket routes — also under /api/v1
# ------------------------------------------------------------------

app.include_router(ws_alerts.router, prefix=API_V1_PREFIX, tags=["websocket"])
