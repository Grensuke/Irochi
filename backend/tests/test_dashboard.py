"""Tests for GET /api/v1/dashboard/summary."""

from unittest.mock import AsyncMock
import pytest
from app.api.dependencies import get_postgres_alert_service
from app.services.postgres_alert_service import PostgresAlertService
from app.main import app
from app.schemas.dashboard import DashboardSummaryResponse

@pytest.fixture(autouse=True)
def override_alert_service():
    mock_service = AsyncMock(spec=PostgresAlertService)
    mock_service.get_dashboard_summary.return_value = DashboardSummaryResponse(
        total_alerts=10,
        critical_count=2,
        high_count=3,
        medium_count=4,
        low_count=1,
        info_count=0,
        by_threat_type={"volumetric_ddos": 10},
        by_detector={"ddos_detector": 10},
        recent_alerts=[{"alert_id": "123", "timestamp": "2024-01-01T00:00:00Z", "threat_type": "volumetric_ddos", "detector_id": "ddos_detector", "severity": "high", "status": "new", "entity_type": "source", "entity_key": "ip", "first_seen_at": "2024-01-01T00:00:00Z", "last_seen_at": "2024-01-01T00:00:00Z", "evidence_summary": "test", "confidence": 0.9}]
    )
    app.dependency_overrides[get_postgres_alert_service] = lambda: mock_service
    yield
    app.dependency_overrides.clear()
def test_dashboard_summary_returns_200(client):
    """Dashboard summary endpoint returns HTTP 200."""
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200


def test_dashboard_summary_structure(client):
    """Dashboard summary has all required fields."""
    data = client.get("/api/v1/dashboard/summary").json()
    required_fields = {
        "total_alerts",
        "critical_count",
        "high_count",
        "medium_count",
        "low_count",
        "info_count",
        "by_threat_type",
        "by_detector",
        "recent_alerts",
    }
    assert required_fields.issubset(data.keys())


def test_dashboard_summary_counts_consistent(client):
    """Severity counts sum to total_alerts."""
    data = client.get("/api/v1/dashboard/summary").json()
    severity_sum = (
        data["critical_count"]
        + data["high_count"]
        + data["medium_count"]
        + data["low_count"]
        + data["info_count"]
    )
    assert severity_sum == data["total_alerts"]


def test_dashboard_summary_has_threat_breakdown(client):
    """by_threat_type contains threat type keys."""
    data = client.get("/api/v1/dashboard/summary").json()
    assert isinstance(data["by_threat_type"], dict)
    assert len(data["by_threat_type"]) > 0


def test_dashboard_summary_has_detector_breakdown(client):
    """by_detector contains detector ID keys."""
    data = client.get("/api/v1/dashboard/summary").json()
    assert isinstance(data["by_detector"], dict)
    assert len(data["by_detector"]) > 0


def test_dashboard_summary_recent_alerts(client):
    """recent_alerts is a non-empty list of alert objects."""
    data = client.get("/api/v1/dashboard/summary").json()
    assert isinstance(data["recent_alerts"], list)
    assert len(data["recent_alerts"]) > 0
    assert "alert_id" in data["recent_alerts"][0]
