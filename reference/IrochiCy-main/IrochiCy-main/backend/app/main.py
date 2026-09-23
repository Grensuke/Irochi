"""
SIH26145 — FastAPI application factory.
All services connect to localhost.
"""

from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import structlog
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.responses import Response

from app.alert_engine.engine import consume_detector_results
from app.alerts.router import router as alerts_router
from app.auth.router import router as auth_router
from app.auth.service import create_initial_admin
from app.config import settings
from app.dashboard.router import router as dashboard_router
from app.database import async_session_factory, engine
from app.dependencies import get_db, get_redis
from app.middleware.logging import LoggingMiddleware
from app.middleware.metrics import MetricsMiddleware, metrics_endpoint
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.redis_client import close_redis, get_redis_client, init_redis
from app.threats.router import router as threats_router
from app.users.router import router as users_router
from app.websocket.connection_manager import manager as ws_manager
from app.websocket.redis_subscriber import subscribe_to_alerts
from app.websocket.router import router as ws_router

logger = structlog.get_logger(__name__)

# Background tasks tracked for graceful shutdown
_background_tasks: list[asyncio.Task] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""

    # ── STARTUP ──────────────────────────────────────────────────
    # 1. Initialize Redis
    redis = await init_redis()
    logger.info("redis_connected", host=settings.redis_host)

    # 2. Create initial admin user if no users exist
    async with async_session_factory() as db:
        await create_initial_admin(db)

    # 3. Start Redpanda consumer background task (skip in tests)
    if settings.environment != "test":
        consumer_task = asyncio.create_task(
            consume_detector_results(async_session_factory, redis)
        )
        _background_tasks.append(consumer_task)

    # 4. Start Redis Pub/Sub subscriber background task (skip in tests)
    if settings.environment != "test":
        subscriber_task = asyncio.create_task(
            subscribe_to_alerts(redis, ws_manager)
        )
        _background_tasks.append(subscriber_task)

    logger.info(
        "sih26145_backend_started",
        message="SIH26145 backend started. All services on localhost.",
        environment=settings.environment,
    )

    yield

    # ── SHUTDOWN ─────────────────────────────────────────────────
    logger.info("sih26145_backend_shutting_down")

    # 5. Cancel background tasks with 5-second timeout
    for task in _background_tasks:
        task.cancel()
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=5.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass
        except Exception as exc:
            logger.warning("task_shutdown_error", error=str(exc))
    _background_tasks.clear()

    # 6. Close all WebSocket connections (1001 = going away)
    await ws_manager.close_all(code=1001)

    # 7. Close Redis connection pool
    await close_redis()

    # 8. Dispose SQLAlchemy engine connection pool
    await engine.dispose()

    logger.info("sih26145_backend_shut_down_cleanly")


# ── App creation ─────────────────────────────────────────────────
app = FastAPI(
    title="SIH26145 API",
    version="1.0.0",
    description="Network Threat Detection — Security Intelligence Hub",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ── Middleware stack (order matters — first added = outermost) ────
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RateLimitMiddleware)


# ── Routers ──────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(alerts_router)
app.include_router(dashboard_router)
app.include_router(threats_router)
app.include_router(users_router)
app.include_router(ws_router)


# ── Health check ─────────────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health_check(
    db=Depends(get_db),
    redis=Depends(get_redis),
) -> dict:
    """Check connectivity to PostgreSQL and Redis."""
    postgres_ok = False
    redis_ok = False

    try:
        result = await db.execute(text("SELECT 1"))
        postgres_ok = result.scalar_one() == 1
    except Exception as exc:
        logger.warning("health_postgres_fail", error=str(exc))

    try:
        redis_ok = await redis.ping()
    except Exception as exc:
        logger.warning("health_redis_fail", error=str(exc))

    overall = "ok" if (postgres_ok and redis_ok) else "degraded"
    return {
        "status": overall,
        "postgres": postgres_ok,
        "redis": redis_ok,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Metrics endpoint ────────────────────────────────────────────
@app.get("/metrics", tags=["system"])
async def get_metrics() -> Response:
    """Prometheus metrics endpoint."""
    return metrics_endpoint()


# ── Global exception handlers ───────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "request_id": request_id},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "request_id": request_id,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.error(
        "unhandled_exception",
        request_id=request_id,
        path=request.url.path,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal error", "request_id": request_id},
    )
