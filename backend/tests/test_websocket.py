"""Tests for WS /api/v1/ws/alerts (dummy WebSocket)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_websocket_connects_and_receives_backfill():
    """WebSocket connects and receives backfill alerts followed by backfill_complete."""
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/alerts") as ws:
        messages = []
        # Read backfill messages + the backfill_complete marker
        # Config: WS_BACKFILL_COUNT = 5, so expect 5 backfill + 1 complete = 6
        for _ in range(6):
            msg = ws.receive_json()
            messages.append(msg)

        # Verify backfill alerts
        backfill_msgs = [m for m in messages if m["type"] == "backfill"]
        assert len(backfill_msgs) == 5

        # Each backfill message should have an alert
        for msg in backfill_msgs:
            assert msg["alert"] is not None
            assert "alert_id" in msg["alert"]
            assert "threat_type" in msg["alert"]
            assert "detector_id" in msg["alert"]

        # Verify backfill_complete marker
        complete_msgs = [m for m in messages if m["type"] == "backfill_complete"]
        assert len(complete_msgs) == 1
        assert complete_msgs[0]["alert"] is None


def test_websocket_receives_live_alert_after_backfill():
    """After backfill, WebSocket receives live alerts."""
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/alerts") as ws:
        # Drain backfill (5 alerts + 1 complete)
        for _ in range(6):
            ws.receive_json()

        # Read the first live alert
        live_msg = ws.receive_json()
        assert live_msg["type"] == "live"
        assert live_msg["alert"] is not None
        assert live_msg["alert"]["alert_id"].startswith("LIVE-")
        assert live_msg["alert"]["status"] == "new"


def test_websocket_message_types_are_valid():
    """All WebSocket messages have valid type values."""
    valid_types = {"backfill", "live", "backfill_complete"}
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/alerts") as ws:
        # Read backfill + complete + 1 live = 7 messages
        for _ in range(7):
            msg = ws.receive_json()
            assert msg["type"] in valid_types, (
                f"Invalid message type: {msg['type']}"
            )
