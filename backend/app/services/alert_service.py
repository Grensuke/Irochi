"""
Alert service — interface + mock implementation.

DUMMY PHASE: Returns mock data from app.mock.data.
FUTURE: Replace MockAlertService with a real implementation
backed by PostgreSQL queries.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from app.mock.data import (
    LIVE_ALERT_TEMPLATES,
    MOCK_ALERTS,
    MOCK_ALERTS_BY_ID,
)
from app.schemas.alerts import AlertResponse, AlertStatus


# ------------------------------------------------------------------
# Interface — defines the contract for all alert service impls
# ------------------------------------------------------------------


class AlertService(ABC):
    """Abstract alert service interface.

    Future implementations (e.g. PostgreSQL-backed) must implement
    these methods.
    """

    @abstractmethod
    def get_alerts(self) -> list[AlertResponse]:
        """Return all alerts."""
        ...

    @abstractmethod
    def get_alert_by_id(self, alert_id: str) -> AlertResponse | None:
        """Return a single alert by ID, or None if not found."""
        ...

    @abstractmethod
    def get_backfill_alerts(self, count: int) -> list[AlertResponse]:
        """Return a batch of alerts for WebSocket backfill simulation."""
        ...

    @abstractmethod
    def generate_live_alert(self, index: int) -> AlertResponse:
        """Generate a new mock alert for WebSocket live simulation."""
        ...


# ------------------------------------------------------------------
# Mock implementation
# ------------------------------------------------------------------


class MockAlertService(AlertService):
    """Mock alert service using static data."""

    def get_alerts(self) -> list[AlertResponse]:
        return list(MOCK_ALERTS)

    def get_alert_by_id(self, alert_id: str) -> AlertResponse | None:
        return MOCK_ALERTS_BY_ID.get(alert_id)

    def get_backfill_alerts(self, count: int) -> list[AlertResponse]:
        """Return the first `count` alerts as simulated backfill."""
        return MOCK_ALERTS[:count]

    def generate_live_alert(self, index: int) -> AlertResponse:
        """Generate a deterministic live alert from templates.

        Uses index to cycle through templates for predictability
        during frontend development.
        """
        template = LIVE_ALERT_TEMPLATES[index % len(LIVE_ALERT_TEMPLATES)]
        return AlertResponse(
            alert_id=f"LIVE-{index + 1:03d}-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            status=AlertStatus.NEW,
            **template,
        )


# ------------------------------------------------------------------
# Service instance — swap this for a real implementation later
# ------------------------------------------------------------------

alert_service: AlertService = MockAlertService()
