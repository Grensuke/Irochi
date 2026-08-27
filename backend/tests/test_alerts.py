"""Tests for GET /api/v1/alerts and GET /api/v1/alerts/{alert_id}."""


def test_alerts_returns_200(client):
    """Alerts endpoint returns HTTP 200."""
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200


def test_alerts_returns_list_with_total(client):
    """Alerts response has 'alerts' list and 'total' count."""
    data = client.get("/api/v1/alerts").json()
    assert "alerts" in data
    assert "total" in data
    assert isinstance(data["alerts"], list)
    assert data["total"] == len(data["alerts"])
    assert data["total"] > 0


def test_alert_structure(client):
    """Each alert has the required presentation fields."""
    data = client.get("/api/v1/alerts").json()
    alert = data["alerts"][0]
    required_fields = {
        "alert_id",
        "timestamp",
        "threat_type",
        "detector_id",
        "severity",
        "confidence",
        "evidence_summary",
        "status",
    }
    assert required_fields.issubset(alert.keys())


def test_alert_threat_types_valid(client):
    """All alerts use valid threat_type values."""
    valid_types = {
        "volumetric_ddos",
        "c2_beaconing",
        "dga_dns_tunnel",
        "encrypted_malware",
        "recon_portscan",
        "data_exfiltration",
    }
    data = client.get("/api/v1/alerts").json()
    for alert in data["alerts"]:
        assert alert["threat_type"] in valid_types, (
            f"Invalid threat_type: {alert['threat_type']}"
        )


def test_alert_detector_ids_valid(client):
    """All alerts use valid detector_id values."""
    valid_ids = {
        "ddos_detector",
        "recon_detector",
        "dns_dga_tunnel_detector",
        "tls_c2_detector",
        "exfiltration_detector",
    }
    data = client.get("/api/v1/alerts").json()
    for alert in data["alerts"]:
        assert alert["detector_id"] in valid_ids, (
            f"Invalid detector_id: {alert['detector_id']}"
        )


def test_alert_by_id_returns_alert(client):
    """GET /api/v1/alerts/{alert_id} returns the correct alert."""
    response = client.get("/api/v1/alerts/ALERT-001")
    assert response.status_code == 200
    data = response.json()
    assert data["alert_id"] == "ALERT-001"


def test_alert_by_id_not_found(client):
    """GET /api/v1/alerts/{alert_id} returns 404 for missing alert."""
    response = client.get("/api/v1/alerts/NONEXISTENT-999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Alert not found"


def test_all_six_threat_types_covered(client):
    """Mock alerts cover all six threat capabilities."""
    expected = {
        "volumetric_ddos",
        "c2_beaconing",
        "dga_dns_tunnel",
        "encrypted_malware",
        "recon_portscan",
        "data_exfiltration",
    }
    data = client.get("/api/v1/alerts").json()
    actual = {a["threat_type"] for a in data["alerts"]}
    assert expected == actual, f"Missing threat types: {expected - actual}"


def test_all_five_detectors_covered(client):
    """Mock alerts cover all five detector modules."""
    expected = {
        "ddos_detector",
        "recon_detector",
        "dns_dga_tunnel_detector",
        "tls_c2_detector",
        "exfiltration_detector",
    }
    data = client.get("/api/v1/alerts").json()
    actual = {a["detector_id"] for a in data["alerts"]}
    assert expected == actual, f"Missing detectors: {expected - actual}"
