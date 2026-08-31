import asyncio
import os
import uuid

import pytest
import pytest_asyncio

from app.core.config import REDIS_URL
from app.services.state.redis_client import RedisStateService


@pytest_asyncio.fixture
async def redis_service():
    """Provides a started RedisStateService for integration testing."""
    service = RedisStateService(REDIS_URL)
    await service.start()
    yield service
    # Clean up test keys explicitly or just stop
    await service.stop()


@pytest.mark.asyncio
async def test_redis_connection_and_stop():
    """Test basic client connectivity and graceful shutdown."""
    service = RedisStateService(REDIS_URL)
    await service.start()
    assert service._client is not None
    assert await service._client.ping() is True
    await service.stop()
    assert service._client is None


@pytest.mark.asyncio
async def test_increment_hash_fields(redis_service: RedisStateService):
    """Test atomic hash increments for sliding windows/counters."""
    test_key = f"test:feature:source:10.0.0.1:bucket:{uuid.uuid4()}"

    await redis_service.increment_hash_fields(
        test_key,
        {"total_packets": 10, "total_bytes": 1024}
    )

    # Read back using raw client to verify
    data = await redis_service._client.hgetall(test_key)
    assert data["total_packets"] == "10"
    assert data["total_bytes"] == "1024"

    # Increment again
    await redis_service.increment_hash_fields(
        test_key,
        {"total_packets": 5, "total_bytes": 512}
    )
    data = await redis_service._client.hgetall(test_key)
    assert data["total_packets"] == "15"
    assert data["total_bytes"] == "1536"

    await redis_service._client.delete(test_key)


@pytest.mark.asyncio
async def test_correlation_state(redis_service: RedisStateService):
    """Test setting and getting short-lived correlation state."""
    test_key = f"test:feature:connection:{uuid.uuid4()}:correlation"

    await redis_service.set_correlation(
        test_key,
        {"tls_ja3": "abc123def456", "bytes": "500"},
        ttl_seconds=60
    )

    data = await redis_service.get_correlation(test_key)
    assert data["tls_ja3"] == "abc123def456"
    assert data["bytes"] == "500"

    # Verify TTL was set (should be > 0 and <= 60)
    ttl = await redis_service._client.ttl(test_key)
    assert 0 < ttl <= 60

    await redis_service._client.delete(test_key)


@pytest.mark.asyncio
async def test_add_distinct(redis_service: RedisStateService):
    """Test HyperLogLog distinct addition."""
    test_key = f"test:feature:source:10.0.0.2:window:{uuid.uuid4()}:ports"

    await redis_service.add_distinct(test_key, "443")
    await redis_service.add_distinct(test_key, "80")
    await redis_service.add_distinct(test_key, "443")  # Duplicate

    count = await redis_service._client.pfcount(test_key)
    assert count == 2

    await redis_service._client.delete(test_key)


@pytest.mark.asyncio
async def test_directional_pair_identity_support(redis_service: RedisStateService):
    """
    Test that the Redis wrapper supports string serializations of
    the locked directional pair identity (src_ip, dst_ip).
    WP-C does NOT hardcode the exact delimiter, but validates support.
    """
    # Simulate a Feature/Window layer passing a serialized key
    src_ip = "192.168.1.100"
    dst_ip = "10.0.0.50"

    # Using an arbitrary delimiter purely for the test
    test_key = f"test:feature:pair:{src_ip}|{dst_ip}:tier1"

    await redis_service.increment_hash_fields(
        test_key,
        {"count": 1}
    )

    data = await redis_service._client.hgetall(test_key)
    assert data["count"] == "1"

    await redis_service._client.delete(test_key)
