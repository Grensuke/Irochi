import asyncio
import json
import random
import time
from datetime import datetime, timedelta
from uuid import uuid4

import httpx
import pytest
import websockets
from aiokafka import AIOKafkaProducer

from tests.e2e.conftest import WS_BASE
from tests.e2e.helpers import build_detector_result, poll_for_alert

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_01_health_check_all_services(live_client: httpx.AsyncClient):
    """Verify all backend services are healthy."""
    response = await live_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["postgres"] is True
    assert data["redis"] is True


@pytest.mark.asyncio
async def test_02_inject_ddos_detector_result_creates_alert(
    live_client: httpx.AsyncClient,
    admin_headers: dict,
    redpanda_producer: AIOKafkaProducer,
):
    """Inject a DetectorResult, wait for Alert Engine, verify alert in DB."""
    src_ip = f"10.0.0.{random.randint(1, 254)}"
    payload = build_detector_result(
        threat_type="ddos", src_ip=src_ip, confidence=0.92
    )

    await redpanda_producer.send_and_wait(
        "detector.results", json.dumps(payload).encode()
    )

    alert = await poll_for_alert(
        live_client, admin_headers, src_ip=src_ip, threat_type="ddos"
    )

    # Verify the alert fields
    assert alert["threat_type"] == "ddos"
    assert alert["severity"] == "critical"
    assert alert["confidence"] == 0.92
    assert alert["src_ip"] == src_ip
    assert alert["dst_ip"] == "192.168.1.1"
    assert len(alert["evidence"]) == 2  # The build_detector_result map has 2 for ddos
    assert alert["evidence"][0]["signal_name"] == "packet_rate"
    assert alert["evidence"][0]["triggered"] is True
    assert alert["status"] == "new"
    assert alert["ingest_latency_ms"] is not None
    assert alert["ingest_latency_ms"] < 5000

    # Store for later tests if needed
    pytest.shared_alert_id = alert["id"]


@pytest.mark.asyncio
async def test_03_inject_all_five_threat_types(
    live_client: httpx.AsyncClient,
    admin_headers: dict,
    redpanda_producer: AIOKafkaProducer,
):
    """Inject one DetectorResult for each threat type and verify severity mapping."""
    threat_types = {
        "recon": (0.78, "high"),
        "dns_dga": (0.55, "medium"),
        "tls_c2": (0.91, "critical"),
        "exfiltration": (0.33, "low"),
    }

    injections = []
    for t_type, (conf, expected_sev) in threat_types.items():
        src_ip = f"10.0.{random.randint(1, 4)}.{random.randint(1, 254)}"
        payload = build_detector_result(threat_type=t_type, src_ip=src_ip, confidence=conf)
        injections.append((payload, expected_sev))

    # Concurrently inject
    tasks = [
        redpanda_producer.send_and_wait("detector.results", json.dumps(p).encode())
        for p, _ in injections
    ]
    await asyncio.gather(*tasks)

    # Concurrently poll and verify
    async def verify(payload, expected_sev):
        alert = await poll_for_alert(
            live_client, admin_headers, src_ip=payload["src_ip"], threat_type=payload["threat_type"]
        )
        assert alert["severity"] == expected_sev
        assert alert["threat_type"] == payload["threat_type"]

    verify_tasks = [verify(p, s) for p, s in injections]
    await asyncio.gather(*verify_tasks)


@pytest.mark.asyncio
async def test_04_deduplication_prevents_duplicate_alerts(
    live_client: httpx.AsyncClient,
    admin_headers: dict,
    redpanda_producer: AIOKafkaProducer,
):
    """Inject the SAME DetectorResult twice; ensure only one alert is created."""
    src_ip = f"10.255.{random.randint(1, 254)}.{random.randint(1, 254)}"
    payload = build_detector_result(threat_type="ddos", src_ip=src_ip, confidence=0.88)
    
    # Inject twice
    await redpanda_producer.send_and_wait("detector.results", json.dumps(payload).encode())
    await redpanda_producer.send_and_wait("detector.results", json.dumps(payload).encode())
    
    await asyncio.sleep(3.0)
    
    response = await live_client.get("/alerts/", params={"src_ip": src_ip}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_05_websocket_receives_injected_alert_live(
    admin_token: str,
    redpanda_producer: AIOKafkaProducer,
):
    """Verify a connected WebSocket receives real-time alerts."""
    async with websockets.connect(f"{WS_BASE}/ws/alerts?token={admin_token}") as ws:
        connected_msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=5.0))
        assert connected_msg["type"] == "connected"

        src_ip = f"172.16.{random.randint(0,255)}.{random.randint(1,254)}"
        payload = build_detector_result(threat_type="recon", src_ip=src_ip, confidence=0.80)
        
        await redpanda_producer.send_and_wait("detector.results", json.dumps(payload).encode())

        received = False
        deadline = time.time() + 10.0
        while time.time() < deadline:
            try:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=1.0))
                if msg.get("type") == "new_alert" and msg["payload"].get("src_ip") == src_ip:
                    received = True
                    assert "threat_type" in msg["payload"]
                    assert "severity" in msg["payload"]
                    assert "confidence" in msg["payload"]
                    assert "evidence" in msg["payload"]
                    break
            except asyncio.TimeoutError:
                continue

        assert received, "WebSocket did not receive the injected alert within 10 seconds"


@pytest.mark.asyncio
async def test_06_websocket_backfill_accuracy(
    admin_token: str,
    redpanda_producer: AIOKafkaProducer,
):
    """Verify WebSocket backfills missed alerts."""
    cursor_time = datetime.utcnow() - timedelta(minutes=2)
    
    src_ips = [f"192.168.100.{i}" for i in range(1, 6)]
    tasks = []
    for ip in src_ips:
        payload = build_detector_result(threat_type="dns_dga", src_ip=ip, confidence=0.7)
        tasks.append(redpanda_producer.send_and_wait("detector.results", json.dumps(payload).encode()))
    await asyncio.gather(*tasks)
    
    await asyncio.sleep(3.0)  # wait for Alert Engine to process
    
    async with websockets.connect(f"{WS_BASE}/ws/alerts?token={admin_token}&last_cursor={cursor_time.isoformat()}") as ws:
        backfill_alerts = []
        saw_connected = False
        saw_complete = False
        deadline = time.time() + 15.0
        while time.time() < deadline:
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=2.0))
            if msg["type"] == "backfill":
                backfill_alerts.append(msg["payload"])
            elif msg["type"] == "backfill_complete":
                saw_complete = True
            elif msg["type"] == "connected":
                saw_connected = True
                
            if saw_complete and saw_connected:
                break
                
        assert saw_complete, "Did not receive backfill_complete"
        assert saw_connected, "Did not receive connected"
        # We injected 5, there might be more from other tests, but at least 5
        assert len(backfill_alerts) >= 5
        
        # Verify no duplicates
        alert_ids = [a["id"] for a in backfill_alerts]
        assert len(alert_ids) == len(set(alert_ids))
        
        # Verify all 5 injected IPs are in the backfill
        received_ips = [a["src_ip"] for a in backfill_alerts]
        for ip in src_ips:
            assert ip in received_ips


@pytest.mark.asyncio
async def test_07_websocket_status_change_broadcast(
    live_client: httpx.AsyncClient,
    admin_token: str,
    admin_headers: dict,
):
    """Verify status changes are broadcasted over WebSocket."""
    alert_id = getattr(pytest, "shared_alert_id", None)
    assert alert_id is not None, "Missing alert from test_02"
    
    async with websockets.connect(f"{WS_BASE}/ws/alerts?token={admin_token}") as ws:
        await asyncio.wait_for(ws.recv(), timeout=5.0)  # Consume connected msg
        
        response = await live_client.patch(
            f"/alerts/{alert_id}/status",
            json={"status": "acknowledged", "note": "e2e test"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        
        deadline = time.time() + 10.0
        received = False
        while time.time() < deadline:
            try:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=1.0))
                if msg.get("type") == "alert_status_changed" and msg["payload"].get("alert_id") == alert_id:
                    assert msg["payload"]["new_status"] == "acknowledged"
                    received = True
                    break
            except asyncio.TimeoutError:
                continue
                
        assert received, "Did not receive status change broadcast"
