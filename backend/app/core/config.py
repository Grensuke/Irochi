"""
Vibhinetra backend — application configuration.

DUMMY PHASE: Configuration is minimal. Production configuration
(database URLs, Redis, Redpanda, JWT secrets, etc.) will be
added when the real pipeline is implemented.
"""

from __future__ import annotations

import os

# --- Application metadata ---

APP_TITLE = "Vibhinetra"
APP_DESCRIPTION = (
    "Passive, real-time network threat-detection and "
    "security-intelligence system — SIH26145"
)
APP_VERSION = "0.1.0-dummy"

# --- API versioning & Deployment ---

API_V1_PREFIX = "/api/v1"
BACKEND_ENV = os.getenv("BACKEND_ENV", "development")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
DISABLE_PIPELINE = os.getenv("DISABLE_PIPELINE", "false").lower() == "true"
ENABLE_API_DOCS = os.getenv("ENABLE_API_DOCS", "true").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")

if BACKEND_ENV == "production":
    if SECRET_KEY == "change-me":
        raise ValueError("SECRET_KEY must be set in production")
    if os.getenv("POSTGRES_PASSWORD", "change-me") == "change-me":
        raise ValueError("POSTGRES_PASSWORD must be set in production")

_cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "*")
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in _cors_origins.split(",") if origin.strip()]

# --- WebSocket dummy settings ---

WS_BACKFILL_COUNT = 5
"""Number of mock alerts sent as simulated backfill on WebSocket connect."""

WS_LIVE_INTERVAL_SECONDS = 4.0
"""Seconds between mock live alert emissions on the WebSocket."""

WS_LIVE_MAX_ALERTS = 50
"""Maximum number of live alerts to emit before stopping (prevents runaway loops)."""

# --- PostgreSQL ---
POSTGRES_USER = os.getenv("POSTGRES_USER", "vibhinetra")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "change-me")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "vibhinetra")

_constructed_url = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
raw_url = os.getenv("POSTGRES_URL", os.getenv("DATABASE_URL", _constructed_url))
POSTGRES_URL = raw_url.replace("postgres://", "postgresql+asyncpg://").replace("postgresql://", "postgresql+asyncpg://")

# --- Redis ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_URL = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}")

# --- Redpanda ---
REDPANDA_BROKER = os.getenv("REDPANDA_BROKER", "localhost:19092")
REDPANDA_CONSUMER_GROUP = os.getenv("REDPANDA_CONSUMER_GROUP", "vibhinetra-pipeline-group-v2")
# Note: In a real environment, this might come from a robust config. For MVP we use comma-separated env var.
_default_topics = "vibhinetra.events.connection.v1,vibhinetra.events.dns.v1,vibhinetra.events.tls.v1"
REDPANDA_TOPICS = [t.strip() for t in os.getenv("REDPANDA_TOPICS", _default_topics).split(",") if t.strip()]

# --- Models ---
VIBHINETRA_DGA_MODEL_PATH = os.getenv("VIBHINETRA_DGA_MODEL_PATH", "/app/models/dns_dga_model_v1.joblib")
VIBHINETRA_EXFIL_MODEL_PATH = os.getenv("VIBHINETRA_EXFIL_MODEL_PATH", "/app/models/exfil_model_v1.joblib")
