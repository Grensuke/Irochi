"""
Dashboard service — interface + mock implementation.

DUMMY PHASE: Computes summary metrics from mock alert data.
FUTURE: Replace with real queries against PostgreSQL / Redis hot state.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter

from app.schemas.alerts import AlertResponse
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.alert_service import alert_service


# ------------------------------------------------------------------
# Interface
# ------------------------------------------------------------------


class DashboardService(ABC):
    """Abstract dashboard service interface."""

    @abstractmethod
    def get_summary(self) -> DashboardSummaryResponse:
        """Return dashboard summary metrics."""
        ...


# ------------------------------------------------------------------
# Mock implementation
# ------------------------------------------------------------------


class MockDashboardService(DashboardService):
    """Mock dashboard service — derives metrics from mock alert data."""

    def get_summary(self) -> DashboardSummaryResponse:
        alerts: list[AlertResponse] = alert_service.get_alerts()

        severity_counts = Counter(a.severity.value for a in alerts)
        threat_counts = Counter(a.threat_type.value for a in alerts)
        detector_counts = Counter(a.detector_id.value for a in alerts)

        return DashboardSummaryResponse(
            total_alerts=len(alerts),
            critical_count=severity_counts.get("critical", 0),
            high_count=severity_counts.get("high", 0),
            medium_count=severity_counts.get("medium", 0),
            low_count=severity_counts.get("low", 0),
            info_count=severity_counts.get("info", 0),
            by_threat_type=dict(threat_counts),
            by_detector=dict(detector_counts),
            recent_alerts=alerts[:5],
        )


# ------------------------------------------------------------------
# Service instance
# ------------------------------------------------------------------

dashboard_service: DashboardService = MockDashboardService()
