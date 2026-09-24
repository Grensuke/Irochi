"""Pytest fixtures for Vibhinetra backend tests."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from app.main import app


from unittest.mock import AsyncMock, patch

@pytest.fixture(autouse=True)
def mock_redis_services():
    """Mock Redis services so tests can run without a live Redis server."""
    async def mock_consume(*args, **kwargs):
        if False: yield

    try:
        from fakeredis import FakeAsyncRedis
        fake_redis = FakeAsyncRedis(decode_responses=True)
        fake_redis.ping = AsyncMock(return_value=True)
    except ImportError:
        fake_redis = AsyncMock()
        fake_redis.ping = AsyncMock(return_value=True)

    with patch("app.services.state.redis_client.Redis.from_url", return_value=fake_redis), \
         patch("app.services.redis_pubsub.RedisPubSubService.start", new_callable=AsyncMock):
        yield

@pytest.fixture
def client():
    """Synchronous test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c

