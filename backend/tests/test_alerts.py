"""Tests for GET /api/v1/alerts and GET /api/v1/alerts/{alert_id}."""


import pytest
from unittest.mock import AsyncMock
from app.schemas.alerts import AlertListResponse, AlertResponse
from app.api.dependencies import get_postgres_alert_service
from app.services.postgres_alert_service import PostgresAlertService
from app.mock.data import MOCK_ALERTS
from app.main import app

@pytest.fixture(autouse=True)
def override_alert_service():
    mock_service = AsyncMock(spec=PostgresAlertService)

    class MockOrmAlert:
        def __init__(self, data):
            # If data is already a dict, use it. If it's a Pydantic model, model_dump it.
            # In our mock/data.py, MOCK_ALERTS elements are AlertResponse objects.
            dumped = data.model_dump() if hasattr(data, "model_dump") else data
            self.alert_id = dumped["alert_id"]
            self.last_seen_at = dumped["timestamp"]
            self.threat_type = dumped["threat_type"]
            self.detector_id = dumped["detector_id"]
            self.severity = dumped["severity"]
            self.confidence = dumped.get("confidence")
            self.entity_type = "source" if dumped.get("src_ip") else "destination"
            self.entity_key = dumped.get("src_ip") or dumped.get("dst_ip") or "unknown"
            self.evidence_summary = dumped["evidence_summary"]
            self.status = dumped["status"]

    mock_service.list_alerts.return_value = [MockOrmAlert(a) for a in MOCK_ALERTS]

    async def mock_get_alert(uid):
        if str(uid) == "11111111-1111-1111-1111-111111111111":
            # Return the first mock alert, but modify its ID to match the UUID so the test passes
            data = MOCK_ALERTS[0].model_dump() if hasattr(MOCK_ALERTS[0], "model_dump") else dict(MOCK_ALERTS[0])
            data["alert_id"] = str(uid)
            return MockOrmAlert(data)
        return None

    mock_service.get_alert = mock_get_alert

    app.dependency_overrides[get_postgres_alert_service] = lambda: mock_service
    yield
    app.dependency_overrides.clear()


def test_alerts_returns_200(client):
    """Alerts endpoint returns HTTP 200."""
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200


def test_alerts_returns_list_with_total(client):
    """Alerts response has 'alerts' list and 'total' count."""
    response = client.get("/api/v1/alerts")
    data = response.json()
    assert "alerts" in data
    assert "total" in data
    assert data["total"] == len(data["alerts"])


def test_alert_structure(client):
    """Each alert in the list matches the expected Alert schema."""
    response = client.get("/api/v1/alerts")
    alerts = response.json()["alerts"]
    assert len(alerts) > 0

    for alert in alerts:
        assert "alert_id" in alert
        assert "timestamp" in alert
        assert "threat_type" in alert
        assert "detector_id" in alert
        assert "severity" in alert
        assert "status" in alert


def test_alert_threat_types_valid(client):
    """All alerts have a valid SIH threat type."""
    valid_threats = {
        "volumetric_ddos",
        "c2_beaconing",
        "dga_dns_tunnel",
        "encrypted_malware",
        "recon_portscan",
        "data_exfiltration"
    }

    response = client.get("/api/v1/alerts")
    alerts = response.json()["alerts"]

    for alert in alerts:
        assert alert["threat_type"] in valid_threats, (
            f"Invalid threat type: {alert['threat_type']}"
        )


def test_alert_detector_ids_valid(client):
    """All alerts map to one of the 5 logical detectors."""
    valid_detectors = {
        "ddos_detector",
        "tls_c2_detector",
        "dns_dga_tunnel_detector",
        "recon_detector",
        "exfiltration_detector"
    }

    response = client.get("/api/v1/alerts")
    alerts = response.json()["alerts"]

    for alert in alerts:
        assert alert["detector_id"] in valid_detectors, (
            f"Invalid detector ID: {alert['detector_id']}"
        )


def test_alert_by_id_returns_alert(client):
    """GET /api/v1/alerts/{alert_id} returns the correct alert."""
    test_uuid = "11111111-1111-1111-1111-111111111111"
    response = client.get(f"/api/v1/alerts/{test_uuid}")
    assert response.status_code == 200
    data = response.json()
    assert data["alert_id"] == test_uuid


def test_alert_by_id_not_found(client):
    """GET /api/v1/alerts/{alert_id} returns 404 for missing alert."""
    test_uuid = "99999999-9999-9999-9999-999999999999"
    response = client.get(f"/api/v1/alerts/{test_uuid}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Alert not found"

def test_alert_by_id_invalid_format(client):
    """GET /api/v1/alerts/{alert_id} returns 400 for invalid UUID."""
    response = client.get("/api/v1/alerts/ALERT-001")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid alert ID format"


def test_all_six_threat_types_covered(client):
    """Mock alerts cover all six threat capabilities."""
    response = client.get("/api/v1/alerts")
    alerts = response.json()["alerts"]
    observed_threats = {alert["threat_type"] for alert in alerts}

    expected_threats = {
        "volumetric_ddos",
        "c2_beaconing",
        "dga_dns_tunnel",
        "encrypted_malware",
        "recon_portscan",
        "data_exfiltration"
    }
    assert observed_threats == expected_threats


def test_all_five_detectors_covered(client):
    """Mock alerts cover all five logical detectors."""
    response = client.get("/api/v1/alerts")
    alerts = response.json()["alerts"]
    observed_detectors = {alert["detector_id"] for alert in alerts}

    expected_detectors = {
        "ddos_detector",
        "tls_c2_detector",
        "dns_dga_tunnel_detector",
        "recon_detector",
        "exfiltration_detector"
    }
    assert observed_detectors == expected_detectors
