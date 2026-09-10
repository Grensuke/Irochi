"""Tests for WS /api/v1/ws/alerts (WebSocket)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.dependencies import get_redis_pubsub
from app.services.postgres_alert_service import PostgresAlertService
from app.services.redis_pubsub import RedisPubSubService
from app.mock.data import MOCK_ALERTS, LIVE_ALERT_TEMPLATES
from unittest.mock import AsyncMock, MagicMock
from app.schemas.alerts import AlertStatus
from datetime import datetime, timezone
import uuid

@pytest.fixture(autouse=True)
def override_ws_dependencies(monkeypatch):
    mock_db = AsyncMock(spec=PostgresAlertService)

    class MockOrmAlert:
        def __init__(self, data):
            self.alert_id = data["alert_id"]
            self.last_seen_at = data["timestamp"]
            self.threat_type = data["threat_type"]
            self.detector_id = data["detector_id"]
            self.severity = data["severity"]
            self.confidence = data.get("confidence")
            self.entity_type = "source" if data.get("src_ip") else "destination"
            self.entity_key = data.get("src_ip") or data.get("dst_ip") or "unknown"
            self.first_seen_at = data.get("first_seen_at") or data["timestamp"]
            self.last_seen_at = data.get("last_seen_at") or data["timestamp"]
            self.resolved_at = data.get("resolved_at")
            self.evidence_summary = data["evidence_summary"]
            self.status = data["status"]

    # We need list_alerts to return in descending time order, websocket route reverses it.
    mock_db.list_alerts.return_value = [MockOrmAlert(a.model_dump() if hasattr(a, "model_dump") else a) for a in MOCK_ALERTS][:5]

    mock_pubsub = AsyncMock(spec=RedisPubSubService)

    async def mock_subscribe_alerts():
        # Yield one live alert
        yield {
            "type": "live",
            "alert": {
                "alert_id": f"LIVE-001-{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "threat_type": "volumetric_ddos",
                "detector_id": "ddos_detector",
                "severity": "high",
                "confidence": 0.9,
                "entity_type": "source",
                "entity_key": "mock",
                "first_seen_at": datetime.now(timezone.utc).isoformat(),
                "last_seen_at": datetime.now(timezone.utc).isoformat(),
                "evidence_summary": "Test live alert",
                "status": "new"
            }
        }
        # Yield another to satisfy any further reads
        yield {
            "type": "live",
            "alert": {
                "alert_id": f"LIVE-002-{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "threat_type": "recon_portscan",
                "detector_id": "recon_detector",
                "severity": "high",
                "confidence": 0.9,
                "entity_type": "source",
                "entity_key": "mock",
                "first_seen_at": datetime.now(timezone.utc).isoformat(),
                "last_seen_at": datetime.now(timezone.utc).isoformat(),
                "evidence_summary": "Test live alert 2",
                "status": "new"
            }
        }
        # Keep connection open indefinitely so the client can receive them
        import asyncio
        await asyncio.sleep(60)

    mock_pubsub.subscribe_alerts = mock_subscribe_alerts

    # Mock the AsyncSessionLocal used in websocket_alerts
    mock_session = AsyncMock()
    # When async with AsyncSessionLocal() is called, return mock_session
    mock_session_factory = MagicMock(return_value=mock_session)
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = False

    # Also patch PostgresAlertService so it uses our mock_db when initialized
    monkeypatch.setattr("app.api.websocket.alerts.AsyncSessionLocal", mock_session_factory)
    monkeypatch.setattr("app.api.websocket.alerts.PostgresAlertService", lambda s: mock_db)

    app.dependency_overrides[get_redis_pubsub] = lambda: mock_pubsub
    yield
    app.dependency_overrides.clear()


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
