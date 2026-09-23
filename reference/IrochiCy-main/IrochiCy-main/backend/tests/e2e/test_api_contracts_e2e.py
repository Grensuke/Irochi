import json
from pathlib import Path

import httpx
import pytest

pytestmark = pytest.mark.e2e

# Load openapi.json at module level
with open(Path(__file__).parent.parent.parent / "openapi.json") as f:
    OPENAPI = json.load(f)


def get_response_schema(path: str, method: str, status_code: int = 200) -> dict:
    """Extracts the JSON schema for a given endpoint and status code from OpenAPI."""
    try:
        # OpenAPI responses could be under content -> application/json -> schema
        schema = OPENAPI["paths"][path][method.lower()]["responses"][str(status_code)]["content"]["application/json"]["schema"]
        
        # Resolve $ref if needed
        if "$ref" in schema:
            ref_path = schema["$ref"].split("/")[1:]
            resolved = OPENAPI
            for p in ref_path:
                resolved = resolved[p]
            return resolved
        return schema
    except KeyError:
        pytest.fail(f"Could not find schema for {method} {path} ({status_code})")


def validate_response_shape(data: dict | list, schema: dict) -> None:
    """Recursively assert all required keys from schema exist in data."""
    if "allOf" in schema or "anyOf" in schema:
        # For simplicity in this test, we skip deep validation of these unions
        return

    # If it's a ref, resolve it (basic resolution for definitions)
    if "$ref" in schema:
        ref_path = schema["$ref"].split("/")[1:]
        resolved = OPENAPI
        for p in ref_path:
            resolved = resolved[p]
        schema = resolved

    if schema.get("type") == "array":
        assert isinstance(data, list)
        if len(data) > 0:
            items_schema = schema.get("items", {})
            for item in data:
                validate_response_shape(item, items_schema)
        return

    if schema.get("type") == "object" or "properties" in schema:
        assert isinstance(data, dict)
        required_keys = schema.get("required", [])
        for key in required_keys:
            assert key in data, f"Required key '{key}' missing from response data"
        
        properties = schema.get("properties", {})
        for key, val in data.items():
            if key in properties:
                validate_response_shape(val, properties[key])


@pytest.mark.asyncio
async def test_alerts_list_shape(live_client: httpx.AsyncClient, admin_headers: dict):
    """Validate /alerts/ response against openapi.json."""
    response = await live_client.get("/alerts/", headers=admin_headers)
    assert response.status_code == 200
    schema = get_response_schema("/alerts/", "get")
    validate_response_shape(response.json(), schema)
    
    # Extra hardcoded checks as requested
    data = response.json()
    for key in ("items", "total", "page", "page_size", "has_next"):
        assert key in data


@pytest.mark.asyncio
async def test_alert_detail_shape(live_client: httpx.AsyncClient, admin_headers: dict):
    """Validate /alerts/{id} response against openapi.json."""
    # Get an alert ID first
    list_resp = await live_client.get("/alerts/", headers=admin_headers)
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert len(items) > 0, "No alerts found to test"
    alert_id = items[0]["id"]
    
    response = await live_client.get(f"/alerts/{alert_id}", headers=admin_headers)
    assert response.status_code == 200
    schema = get_response_schema("/alerts/{alert_id}", "get")
    validate_response_shape(response.json(), schema)
    
    # Extra checks
    data = response.json()
    assert isinstance(data["evidence"], list)
    if data["evidence"]:
        for ev in data["evidence"]:
            assert "signal_name" in ev
            assert "signal_type" in ev
            assert "value" in ev
            assert "triggered" in ev


@pytest.mark.asyncio
async def test_dashboard_summary_shape(live_client: httpx.AsyncClient, admin_headers: dict):
    """Validate /dashboard/summary shape."""
    response = await live_client.get("/dashboard/summary", headers=admin_headers)
    assert response.status_code == 200
    schema = get_response_schema("/dashboard/summary", "get")
    validate_response_shape(response.json(), schema)
    
    data = response.json()
    assert "kpi" in data
    kpi = data["kpi"]
    for key in ("total_alerts_today", "active_threats", "events_per_second", "detectors_active", "pipeline_latency_p95_ms", "alerts_delta_today"):
        assert key in kpi
    assert isinstance(data["top_threats"], list)
    assert isinstance(data["top_source_ips"], list)


@pytest.mark.asyncio
async def test_dashboard_timeline_shape(live_client: httpx.AsyncClient, admin_headers: dict):
    """Validate /dashboard/timeline shape."""
    response = await live_client.get("/dashboard/timeline", headers=admin_headers)
    assert response.status_code == 200
    schema = get_response_schema("/dashboard/timeline", "get")
    validate_response_shape(response.json(), schema)
    
    data = response.json()
    assert isinstance(data["buckets"], list)
    assert len(data["buckets"]) == 24
    for b in data["buckets"]:
        assert "timestamp" in b
        for threat in ("ddos", "recon", "dns_dga", "tls_c2", "exfiltration"):
            assert threat in b
            assert isinstance(b[threat], int)
            assert b[threat] >= 0


@pytest.mark.asyncio
async def test_threats_list_shape(live_client: httpx.AsyncClient, admin_headers: dict):
    """Validate /threats/ shape."""
    response = await live_client.get("/threats/", headers=admin_headers)
    assert response.status_code == 200
    schema = get_response_schema("/threats/", "get")
    validate_response_shape(response.json(), schema)
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 5
    threat_types = set()
    for t in data:
        for key in ("threat_type", "display_name", "description", "signals", "alerts_today", "alerts_7d", "avg_confidence", "detector_status"):
            assert key in t
        threat_types.add(t["threat_type"])
    
    assert threat_types == {"ddos", "recon", "dns_dga", "tls_c2", "exfiltration"}


@pytest.mark.asyncio
async def test_threat_detail_shape(live_client: httpx.AsyncClient, admin_headers: dict):
    """Validate /threats/{threat_type} shape."""
    for threat in ("ddos", "recon", "dns_dga", "tls_c2", "exfiltration"):
        response = await live_client.get(f"/threats/{threat}", headers=admin_headers)
        assert response.status_code == 200
        schema = get_response_schema("/threats/{threat_type}", "get")
        validate_response_shape(response.json(), schema)
        
        data = response.json()
        assert "stat" in data
        assert isinstance(data["confidence_distribution"], list)
        assert len(data["confidence_distribution"]) == 10
        for b in data["confidence_distribution"]:
            assert "bucket_label" in b
            assert "count" in b
        assert isinstance(data["recent_alerts"], list)
        assert len(data["stat"]["signals"]) > 0


@pytest.mark.asyncio
async def test_users_me_shape(live_client: httpx.AsyncClient, analyst_headers: dict):
    """Validate /users/me shape."""
    response = await live_client.get("/users/me", headers=analyst_headers)
    assert response.status_code == 200
    schema = get_response_schema("/users/me", "get")
    validate_response_shape(response.json(), schema)
    
    data = response.json()
    for key in ("id", "username", "full_name", "email", "role", "is_active", "created_at"):
        assert key in data
    assert "password_hash" not in data
