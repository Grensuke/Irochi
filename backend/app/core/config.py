"""
Irochi backend — application configuration.

DUMMY PHASE: Configuration is minimal. Production configuration
(database URLs, Redis, Redpanda, JWT secrets, etc.) will be
added when the real pipeline is implemented.
"""

from __future__ import annotations


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
