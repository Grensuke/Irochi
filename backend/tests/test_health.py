"""Tests for GET /api/v1/health."""


def test_health_returns_200(client):
    """Health endpoint returns HTTP 200."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_returns_ok_status(client):
    """Health endpoint returns {"status": "ok"}."""
    response = client.get("/api/v1/health")
    data = response.json()
    assert data == {"status": "ok"}
