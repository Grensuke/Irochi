import asyncio
import json
import random
import time
from uuid import uuid4

import httpx
import pytest
import websockets
from aiokafka import AIOKafkaProducer

from tests.e2e.conftest import WS_BASE
from tests.e2e.helpers import build_detector_result

pytestmark = [pytest.mark.e2e, pytest.mark.slow]


@pytest.mark.asyncio
async def test_burst_50_detector_results_all_create_alerts(
    live_client: httpx.AsyncClient,
    admin_headers: dict,
    redpanda_producer: AIOKafkaProducer,
):
    """
    Inject 50 DetectorResults concurrently across all 5 threat types.
    Every one must result in an alert (no silent drops).
    Must complete within 60 seconds.
    """
    threat_types = ["ddos", "recon", "dns_dga", "tls_c2", "exfiltration"]
    payloads = []
    
    for _ in range(10):
        for t_type in threat_types:
            src_ip = f"10.100.{random.randint(1, 254)}.{random.randint(1, 254)}"
            conf = round(random.uniform(0.60, 0.99), 2)
            payloads.append(build_detector_result(t_type, src_ip, conf))

    event_ids = {p["event_id"] for p in payloads}

    tasks = [
        redpanda_producer.send_and_wait("detector.results", json.dumps(p).encode())
        for p in payloads
    ]
    await asyncio.gather(*tasks)
    
    start_time = time.time()
    all_found = False
    
    while time.time() - start_time < 60:
        resp = await live_client.get("/alerts/?page_size=100", headers=admin_headers)
        if resp.status_code == 200:
            items = resp.json()["items"]
            found_ids = {a["raw_event_id"] for a in items if a.get("raw_event_id")}
            if event_ids.issubset(found_ids):
                all_found = True
                break
        await asyncio.sleep(2.0)

    elapsed = time.time() - start_time
    assert all_found, f"Not all 50 alerts were created within 60s. Elapsed: {elapsed:.1f}s"
    assert elapsed < 60


@pytest.mark.asyncio
async def test_concurrent_websocket_connections(
    admin_token: str,
    redpanda_producer: AIOKafkaProducer,
):
    """
    Open 10 WebSocket connections simultaneously using the same admin token.
    Inject an alert. All 10 must receive the new_alert message.
    """
    src_ip = f"10.200.{random.randint(1, 254)}.{random.randint(1, 254)}"
    queues = [asyncio.Queue() for _ in range(10)]
    
    async def connect_and_listen(q: asyncio.Queue):
        async with websockets.connect(f"{WS_BASE}/ws/alerts?token={admin_token}") as ws:
            await ws.recv()  # connected message
            try:
                deadline = time.time() + 15.0
                while time.time() < deadline:
                    try:
                        msg_str = await asyncio.wait_for(ws.recv(), timeout=2.0)
                        parsed = json.loads(msg_str)
                        if parsed.get("type") == "new_alert" and parsed.get("payload", {}).get("src_ip") == src_ip:
                            await q.put(parsed)
                            break
                    except asyncio.TimeoutError:
                        continue
            except Exception as e:
                await q.put({"error": str(e)})

    # Start 10 background tasks
    tasks = [asyncio.create_task(connect_and_listen(q)) for q in queues]
    
    # Wait a bit to ensure they are all connected and subscribed to Redis
    await asyncio.sleep(5.0)
    
    payload = build_detector_result("dns_dga", src_ip, 0.85)
    await redpanda_producer.send_and_wait("detector.results", json.dumps(payload).encode())
    
    # Wait for all listeners to finish
    await asyncio.gather(*tasks)
    
    for q in queues:
        assert not q.empty(), "A websocket client received no messages"
        msg = await q.get()
        assert "error" not in msg, f"Websocket client encountered error: {msg['error']}"
        assert msg["type"] == "new_alert"
        assert msg["payload"]["src_ip"] == src_ip


@pytest.mark.asyncio
async def test_rapid_status_transitions_are_serialized(
    live_client: httpx.AsyncClient,
    admin_headers: dict,
    redpanda_producer: AIOKafkaProducer,
):
    """
    PATCH the same alert's status rapidly from 5 concurrent requests.
    Only one valid transition should succeed per step.
    """
    src_ip = f"10.201.{random.randint(1, 254)}.{random.randint(1, 254)}"
    payload = build_detector_result("exfiltration", src_ip, 0.90)
    await redpanda_producer.send_and_wait("detector.results", json.dumps(payload).encode())
    
    start_time = time.time()
    alert_id = None
    while time.time() - start_time < 20:
        resp = await live_client.get("/alerts/", params={"src_ip": src_ip}, headers=admin_headers)
        if resp.json().get("total", 0) > 0:
            alert_id = resp.json()["items"][0]["id"]
            break
        await asyncio.sleep(1.0)
        
    assert alert_id is not None, "Failed to get alert for race condition test"
    
    results = await asyncio.gather(*[
        live_client.patch(
            f"/alerts/{alert_id}/status",
            json={"status": "acknowledged"},
            headers=admin_headers
        )
        for _ in range(5)
    ], return_exceptions=True)
    
    status_codes = [r.status_code for r in results if isinstance(r, httpx.Response)]
    
    # Exactly one should succeed, the rest should be 409
    successes = [s for s in status_codes if s == 200]
    conflicts = [s for s in status_codes if s == 409]
    
    assert len(successes) == 1
    assert len(conflicts) == 4
    
    # Verify exact state
    final_resp = await live_client.get(f"/alerts/{alert_id}", headers=admin_headers)
    assert final_resp.json()["status"] == "acknowledged"


@pytest.mark.asyncio
async def test_dashboard_under_load(live_client: httpx.AsyncClient, admin_headers: dict):
    """
    20 concurrent GET /dashboard/summary requests must all succeed.
    Redis cache must mean no N+1 database queries.
    """
    responses = await asyncio.gather(*[
        live_client.get("/dashboard/summary", headers=admin_headers)
        for _ in range(20)
    ])
    
    for r in responses:
        assert r.status_code == 200
        
    total_alerts = [r.json()["kpi"]["total_alerts_today"] for r in responses]
    
    # All 20 should have exactly the same cached value
    assert len(set(total_alerts)) == 1
