import asyncio
import time
from uuid import uuid4

import httpx
import pytest
import websockets
from jose import jwt

from app.config import settings
from tests.e2e.conftest import WS_BASE

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_unauthenticated_routes_return_401(live_client: httpx.AsyncClient):
    """Every protected route must reject requests with no token."""
    routes = [
        ("GET", "/alerts/"),
        ("GET", "/alerts/00000000-0000-0000-0000-000000000001"),
        ("PATCH", "/alerts/00000000-0000-0000-0000-000000000001/status"),
        ("GET", "/dashboard/summary"),
        ("GET", "/dashboard/kpi"),
        ("GET", "/dashboard/timeline"),
        ("GET", "/threats/"),
        ("GET", "/threats/ddos"),
        ("GET", "/users/me"),
        ("GET", "/users/"),
        ("POST", "/users/"),
    ]

    for method, path in routes:
        response = await live_client.request(method, path)
        assert response.status_code == 401, f"Expected 401 for {method} {path}"

    # WS /ws/alerts
    try:
        async with websockets.connect(f"{WS_BASE}/ws/alerts") as ws:
            pytest.fail("WebSocket connected without token")
    except websockets.exceptions.InvalidStatusCode as e:
        assert e.status_code in (401, 403, 400)


@pytest.mark.asyncio
async def test_analyst_cannot_access_admin_routes(live_client: httpx.AsyncClient, analyst_headers: dict):
    """Analyst JWT must be rejected by admin-only endpoints."""
    dummy_uuid = str(uuid4())
    
    routes = [
        ("GET", "/users/"),
        ("POST", "/users/", {"username": "foo", "password": "bar", "email": "a@b.com", "full_name": "F", "role": "admin"}),
        ("GET", f"/users/{dummy_uuid}"),
        ("PATCH", f"/users/{dummy_uuid}", {"role": "admin"}),
        ("DELETE", f"/users/{dummy_uuid}"),
    ]
    
    for req in routes:
        if len(req) == 2:
            method, path = req
            response = await live_client.request(method, path, headers=analyst_headers)
        else:
            method, path, body = req
            response = await live_client.request(method, path, json=body, headers=analyst_headers)
        assert response.status_code == 403, f"Expected 403 for analyst accessing {method} {path}"


@pytest.mark.asyncio
async def test_invalid_jwt_returns_401(live_client: httpx.AsyncClient):
    """Tampered, malformed, and expired JWTs must all be rejected."""
    # Random string
    resp1 = await live_client.get("/users/me", headers={"Authorization": "Bearer random.string.here"})
    assert resp1.status_code == 401

    # Wrong secret
    wrong_secret_token = jwt.encode({"sub": "admin", "type": "access"}, "wrongsecret", algorithm="HS256")
    resp2 = await live_client.get("/users/me", headers={"Authorization": f"Bearer {wrong_secret_token}"})
    assert resp2.status_code == 401

    # Expired token
    expired_token = jwt.encode(
        {"sub": "admin", "type": "access", "exp": int(time.time()) - 3600},
        settings.jwt_secret_key,
        algorithm="HS256"
    )
    resp3 = await live_client.get("/users/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp3.status_code == 401

    # Nonexistent user
    ghost_token = jwt.encode(
        {"sub": "ghost_user_xyz", "type": "access", "exp": int(time.time()) + 900},
        settings.jwt_secret_key,
        algorithm="HS256"
    )
    resp4 = await live_client.get("/users/me", headers={"Authorization": f"Bearer {ghost_token}"})
    assert resp4.status_code == 401


@pytest.mark.asyncio
async def test_rate_limit_login_endpoint(live_client: httpx.AsyncClient):
    """POST /auth/login must be rate-limited to 10 req/min per IP."""
    # Send 11 rapid requests
    tasks = [
        live_client.post("/auth/login", json={"username": "wrong", "password": "wrong"}, headers={"x-forwarded-for": "10.0.0.99"})
        for _ in range(11)
    ]
    responses = await asyncio.gather(*tasks)
    
    # Sort responses by status code, or just check that exactly one is 429
    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes, "Rate limit did not trigger after 10 requests"
    
    rl_response = next(r for r in responses if r.status_code == 429)
    assert "Rate limit exceeded" in rl_response.json()["detail"]
    assert "X-RateLimit-Limit" in rl_response.headers
    assert "Retry-After" in rl_response.headers or "X-RateLimit-Reset" in rl_response.headers


@pytest.mark.asyncio
async def test_security_headers_present(live_client: httpx.AsyncClient, admin_headers: dict):
    """Every response must include the required security headers."""
    # Unauthenticated
    resp1 = await live_client.get("/health")
    for header in ("x-content-type-options", "x-frame-options", "x-xss-protection", "cache-control"):
        assert header in resp1.headers, f"Missing security header {header} on unauthenticated route"
        if header == "cache-control":
            assert "no-store" in resp1.headers[header]
            
    # Authenticated
    resp2 = await live_client.get("/alerts/", headers=admin_headers)
    for header in ("x-content-type-options", "x-frame-options", "x-xss-protection", "cache-control"):
        assert header in resp2.headers, f"Missing security header {header} on authenticated route"


@pytest.mark.asyncio
async def test_analyst_cannot_change_other_users_password(live_client: httpx.AsyncClient, analyst_headers: dict):
    """Analyst can only change their own password."""
    # Try to change admin's password
    admin_id = getattr(pytest, "admin_user_id", str(uuid4()))
    response = await live_client.post(
        f"/users/{admin_id}/password",
        json={"current_password": "fake", "new_password": "fake"},
        headers=analyst_headers,
    )
    assert response.status_code in (404, 405, 403, 401)


@pytest.mark.asyncio
async def test_status_transition_enforcement(live_client: httpx.AsyncClient, admin_headers: dict):
    """Closed alerts cannot be reopened via the REST API."""
    alerts_resp = await live_client.get("/alerts/", headers=admin_headers)
    assert alerts_resp.status_code == 200
    alerts_data = alerts_resp.json()["items"]
    assert len(alerts_data) > 0, "No alerts available to test transitions"
    
    # Find an alert that is not already closed
    alert_id = None
    for a in alerts_data:
        if a["status"] != "closed":
            alert_id = a["id"]
            break
            
    assert alert_id is not None, "No open alerts found"
    r1 = await live_client.patch(f"/alerts/{alert_id}/status", json={"status": "acknowledged"}, headers=admin_headers)
    assert r1.status_code == 200
    
    r2 = await live_client.patch(f"/alerts/{alert_id}/status", json={"status": "closed"}, headers=admin_headers)
    assert r2.status_code == 200
    
    r3 = await live_client.patch(f"/alerts/{alert_id}/status", json={"status": "acknowledged"}, headers=admin_headers)
    assert r3.status_code == 409
    assert "closed" in r3.json()["detail"].lower() or "transition" in r3.json()["detail"].lower()


@pytest.mark.asyncio
async def test_csv_export_does_not_expose_internals(live_client: httpx.AsyncClient, admin_headers: dict):
    """CSV export must only contain allowed columns."""
    response = await live_client.get("/alerts/export/csv", headers=admin_headers)
    assert response.status_code == 200
    csv_text = response.text
    csv_lines = csv_text.strip().split("\n")
    header_row = csv_lines[0].strip().split(",")
    
    allowed = {"id", "threat_type", "severity", "confidence", "src_ip", "dst_ip",
               "src_port", "dst_port", "protocol", "status", "created_at"}
    
    assert set(header_row) == allowed
    assert "password_hash" not in header_row
    assert "analyst_notes" not in header_row
    assert "evidence" not in header_row


@pytest.mark.asyncio
async def test_websocket_cannot_connect_with_refresh_token(live_client: httpx.AsyncClient):
    """Only access tokens must be accepted by the WebSocket."""
    login_resp = await live_client.post(
        "/auth/login",
        json={"username": settings.initial_admin_username, "password": settings.initial_admin_password},
    )
    assert login_resp.status_code == 200
    refresh_token = login_resp.json()["refresh_token"]
    
    try:
        async with websockets.connect(f"{WS_BASE}/ws/alerts?token={refresh_token}") as ws:
            pytest.fail("WebSocket connected with refresh token")
    except websockets.exceptions.InvalidStatusCode as e:
        assert e.status_code in (401, 403, 400)
