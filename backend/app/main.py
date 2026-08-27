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
from app.core.config import API_V1_PREFIX, APP_DESCRIPTION, APP_TITLE, APP_VERSION

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

# ------------------------------------------------------------------
# Application
# ------------------------------------------------------------------

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
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
