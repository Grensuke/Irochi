import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
import asyncio

import pytest
import pytest_asyncio

from app.models.base import Base
from app.main import app
from app.api.dependencies import get_redis_pubsub
from app.services.redis_pubsub import RedisPubSubService
from app.core import config
from unittest.mock import AsyncMock

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, UUID

@compiles(JSONB, "sqlite")
def compile_jsonb(type_, compiler, **kw):
    return "JSON"

@compiles(UUID, "sqlite")
def compile_uuid(type_, compiler, **kw):
    return "TEXT"

@pytest.fixture(autouse=True)
def setup_test_db():
    import asyncpg
    import asyncio
    async def init_db():
        test_url = "sqlite+aiosqlite:///:memory:"
        engine = create_async_engine(test_url, pool_pre_ping=True)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()
    
    # We must run this in a new loop because setup_test_db is not async
    loop = asyncio.new_event_loop()
    loop.run_until_complete(init_db())
    yield

@pytest.fixture(autouse=True)
def override_redis():
    mock_pubsub = AsyncMock(spec=RedisPubSubService)
    async def mock_subscribe_alerts():
        # Keep connection open indefinitely
        while True:
            await asyncio.sleep(60)
            yield {}
    mock_pubsub.subscribe_alerts = mock_subscribe_alerts
    app.dependency_overrides[get_redis_pubsub] = lambda: mock_pubsub
    yield
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_websocket_releases_db_connection(monkeypatch):
    """
    Ensure the WebSocket endpoint releases its database transaction/connection
    after finishing the backfill and before entering the infinite loop.
    """
    # Create the test DB if it doesn't exist
    import asyncpg
    from urllib.parse import urlparse
    parsed = urlparse(config.POSTGRES_URL)
    sys_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/postgres"
    conn = await asyncpg.connect(sys_url)
    try:
        await conn.execute('CREATE DATABASE vibhinetra_test')
    except asyncpg.exceptions.DuplicateDatabaseError:
        pass
    finally:
        await conn.close()
        
    test_url = config.POSTGRES_URL.rsplit('/', 1)[0] + "/vibhinetra_test"
    setup_engine = create_async_engine(test_url, pool_pre_ping=True)
    
    # Run migrations/table creation for the test DB
    async with setup_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await setup_engine.dispose()
        
    # Delay engine creation to avoid binding to the pytest event loop
    def mock_session_local(*args, **kwargs):
        from sqlalchemy.pool import NullPool
        engine = create_async_engine(test_url, poolclass=NullPool)
        session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
        return session_maker(*args, **kwargs)
        
    monkeypatch.setattr("app.api.websocket.alerts.AsyncSessionLocal", mock_session_local)

    client = TestClient(app)

    with client.websocket_connect("/api/v1/ws/alerts") as ws:
        while True:
            msg = ws.receive_json()
            if msg.get("type") == "backfill_complete":
                break

        def try_truncate():
            import asyncio
            async def run_truncate():
                test_url = config.POSTGRES_URL.rsplit('/', 1)[0] + "/vibhinetra_test"
                engine = create_async_engine(test_url, pool_pre_ping=True)
                async with engine.begin() as conn:
                    await conn.execute(text("SET lock_timeout = '2s';"))
                    await conn.execute(text("TRUNCATE TABLE alerts;"))
                await engine.dispose()
            
            loop = asyncio.new_event_loop()
            loop.run_until_complete(run_truncate())
            loop.close()
        
        try:
            import threading
            t = threading.Thread(target=try_truncate)
            t.start()
            t.join(timeout=4.0)
            if t.is_alive():
                pytest.fail("TRUNCATE timed out! The WebSocket is likely holding a lock.")
        except Exception as e:
            pytest.fail(f"TRUNCATE failed or timed out! The WebSocket is likely holding a lock. Error: {e}")
