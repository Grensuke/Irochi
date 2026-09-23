import asyncio
import json
import random
import time

import httpx
import pytest
import redis.asyncio as redis_asyncio
from aiokafka import AIOKafkaProducer

from app.config import settings
from tests.e2e.helpers import build_detector_result, poll_for_alert

pytestmark = pytest.mark.e2e


@pytest.fixture
async def live_redis():
    """Connected to the live Redis instance."""
    url = f"redis://:{settings.redis_password}@localhost:6379/0"
    client = await redis_asyncio.from_url(url, decode_responses=True)
    yield client
    await client.aclose()


@pytest.mark.asyncio
async def test_dedup_key_set_after_alert_creation(
    redpanda_producer: AIOKafkaProducer,
    live_redis: redis_asyncio.Redis,
):
    """After Alert Engine processes a DetectorResult, a dedup key must exist in Redis."""
    src_ip = f"10.0.101.{random.randint(1, 254)}"
    dst_ip = "192.168.1.1"
    payload = build_detector_result("ddos", src_ip, 0.85, dst_ip=dst_ip)
    
    await redpanda_producer.send_and_wait("detector.results", json.dumps(payload).encode())
    await asyncio.sleep(3.0)
    
    key = f"dedup:ddos:{src_ip}:{dst_ip}"
    exists = await live_redis.exists(key)
    assert exists == 1
    
    ttl = await live_redis.ttl(key)
    assert 0 < ttl <= 120


@pytest.mark.asyncio
async def test_dedup_key_expires(
    redpanda_producer: AIOKafkaProducer,
    live_redis: redis_asyncio.Redis,
):
    """Dedup key must NOT exist more than 120 seconds after creation."""
    src_ip = f"10.0.102.{random.randint(1, 254)}"
    dst_ip = "192.168.1.1"
    payload = build_detector_result("ddos", src_ip, 0.85, dst_ip=dst_ip)
    
    await redpanda_producer.send_and_wait("detector.results", json.dumps(payload).encode())
    await asyncio.sleep(3.0)
    
    key = f"dedup:ddos:{src_ip}:{dst_ip}"
    ttl = await live_redis.ttl(key)
    assert ttl > 0
    assert ttl <= 120


@pytest.mark.asyncio
async def test_dashboard_cache_set_after_summary_request(
    live_client: httpx.AsyncClient,
    admin_headers: dict,
    live_redis: redis_asyncio.Redis,
):
    """After GET /dashboard/summary, Redis must have the cache key."""
    await live_redis.delete("cache:dashboard:summary")
    
    response = await live_client.get("/dashboard/summary", headers=admin_headers)
    assert response.status_code == 200
    
    exists = await live_redis.exists("cache:dashboard:summary")
    assert exists == 1
    
    ttl = await live_redis.ttl("cache:dashboard:summary")
    assert 0 < ttl <= 5


@pytest.mark.asyncio
async def test_dashboard_cache_expires_in_5_seconds(
    live_client: httpx.AsyncClient,
    admin_headers: dict,
    live_redis: redis_asyncio.Redis,
):
    """Cache must expire within 5 seconds."""
    await live_client.get("/dashboard/summary", headers=admin_headers)
    await asyncio.sleep(6.0)
    
    exists = await live_redis.exists("cache:dashboard:summary")
    assert exists == 0


@pytest.mark.asyncio
async def test_alerts_live_pubsub_channel_receives_message(
    redpanda_producer: AIOKafkaProducer,
    live_redis: redis_asyncio.Redis,
):
    """Publishing to 'alerts:live' channel must be receivable by a subscriber."""
    pubsub = live_redis.pubsub()
    await pubsub.subscribe("alerts:live")
    
    # ensure subscription is active before we send
    await asyncio.sleep(0.5)
    
    src_ip = f"10.0.103.{random.randint(1, 254)}"
    payload = build_detector_result("exfiltration", src_ip, 0.6)
    
    await redpanda_producer.send_and_wait("detector.results", json.dumps(payload).encode())
    
    received_msgs = []
    deadline = time.time() + 10.0
    while time.time() < deadline:
        msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
        if msg:
            received_msgs.append(msg)
            break
            
    await pubsub.unsubscribe("alerts:live")
    
    assert len(received_msgs) >= 1
    data_str = received_msgs[0]["data"]
    data = json.loads(data_str)
    
    assert "threat_type" in data
    assert "severity" in data
    assert "src_ip" in data
    # depending on what we publish, check payload
    if "payload" in data:
        assert data["payload"]["src_ip"] == src_ip
    else:
        assert data["src_ip"] == src_ip
