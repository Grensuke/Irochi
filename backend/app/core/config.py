"""
Irochi backend — application configuration.

DUMMY PHASE: Configuration is minimal. Production configuration
(database URLs, Redis, Redpanda, JWT secrets, etc.) will be
added when the real pipeline is implemented.
"""

from __future__ import annotations

import os

# --- Application metadata ---

APP_TITLE = "Irochi"
APP_DESCRIPTION = (
    "Passive, real-time network threat-detection and "
    "security-intelligence system — SIH26145"
)
APP_VERSION = "0.1.0-dummy"

# --- API versioning ---

API_V1_PREFIX = "/api/v1"

# --- WebSocket dummy settings ---

WS_BACKFILL_COUNT = 5
"""Number of mock alerts sent as simulated backfill on WebSocket connect."""

WS_LIVE_INTERVAL_SECONDS = 4.0
"""Seconds between mock live alert emissions on the WebSocket."""

WS_LIVE_MAX_ALERTS = 50
"""Maximum number of live alerts to emit before stopping (prevents runaway loops)."""

# --- PostgreSQL ---
POSTGRES_USER = os.getenv("POSTGRES_USER", "irochi")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "change-me")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "irochi")

POSTGRES_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# --- Redis ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"

# --- Redpanda ---
REDPANDA_BROKER = os.getenv("REDPANDA_BROKER", "localhost:19092")
