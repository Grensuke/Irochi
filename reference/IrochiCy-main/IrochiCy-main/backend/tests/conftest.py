"""
Shared test fixtures for the SIH26145 backend test suite.

Uses a dedicated sih26145_test database on localhost:5432.
Uses fakeredis instead of real Redis.
Each test function gets a rolled-back SAVEPOINT transaction.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator
from uuid import uuid4

os.environ["ENVIRONMENT"] = "test"

import fakeredis.aioredis
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.alerts.models import Alert
from app.auth.utils import hash_password
from app.config import settings
from app.database import Base
from app.dependencies import get_db, get_redis
from app.main import app
from app.users.models import User

# ── Test database URL ────────────────────────────────────────────
# Uses the same credentials but a different database name.
TEST_DB_URL = (
    f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_host}:{settings.postgres_port}/sih26145_test"
)


# ── Event loop ───────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── Test engine (session scope) ──────────────────────────────────

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """
    Create the test database and run schema creation.
    Drops all tables after the session ends.
    """
    # First connect to the default database to create sih26145_test
    admin_url = (
        f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/postgres"
    )
    admin_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'sih26145_test'")
        )
        if result.scalar_one_or_none() is None:
            await conn.execute(text("CREATE DATABASE sih26145_test"))
    await admin_engine.dispose()

    from sqlalchemy.pool import NullPool
    # Create engine for the test database
    engine = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)

    # Create extensions needed by the schema
    async with engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pg_trgm"'))

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Teardown: drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# ── Fake Redis ───────────────────────────────────────────────────

@pytest_asyncio.fixture
async def fake_redis():
    """Provide a fresh fakeredis instance for each test."""
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield r
    await r.aclose()


# ── DB session with SAVEPOINT rollback ───────────────────────────

@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async session wrapped in a SAVEPOINT transaction.
    Everything is rolled back after each test — zero data leaks.
    """
    async with test_engine.connect() as connection:
        transaction = await connection.begin()

        # join_transaction_mode="create_savepoint" ensures that any session.commit()
        # calls inside the app/test only commit a savepoint, leaving the outer
        # transaction intact to be rolled back.
        async with AsyncSession(
            connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint"
        ) as session:
            yield session

        # Rollback the outer transaction (drops everything)
        await transaction.rollback()


# ── Test HTTP client ─────────────────────────────────────────────

@pytest_asyncio.fixture
async def test_client(
    db_session: AsyncSession,
    fake_redis,
) -> AsyncGenerator[AsyncClient, None]:
    """
    httpx AsyncClient wrapping the FastAPI app.
    Overrides get_db and get_redis dependencies.
    """

    async def override_get_db():
        yield db_session

    async def override_get_redis():
        return fake_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# ── User fixtures ────────────────────────────────────────────────

@pytest_asyncio.fixture
async def admin_headers(
    db_session: AsyncSession,
    test_client: AsyncClient,
) -> dict[str, str]:
    """Create an admin user, login, and return auth headers."""
    admin = User(
        id=uuid4(),
        username="test_admin",
        email="test_admin@localhost",
        full_name="Test Admin",
        password_hash=hash_password("TestAdminPass123!"),
        role="admin",
        is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()

    response = await test_client.post(
        "/auth/login",
        json={"username": "test_admin", "password": "TestAdminPass123!"},
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def analyst_headers(
    db_session: AsyncSession,
    test_client: AsyncClient,
) -> dict[str, str]:
    """Create an analyst user, login, and return auth headers."""
    analyst = User(
        id=uuid4(),
        username="test_analyst",
        email="test_analyst@localhost",
        full_name="Test Analyst",
        password_hash=hash_password("TestAnalystPass123!"),
        role="analyst",
        is_active=True,
    )
    db_session.add(analyst)
    await db_session.flush()

    response = await test_client.post(
        "/auth/login",
        json={"username": "test_analyst", "password": "TestAnalystPass123!"},
    )
    assert response.status_code == 200, f"Analyst login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── Sample alert fixture ─────────────────────────────────────────

@pytest_asyncio.fixture
async def sample_alert(db_session: AsyncSession) -> Alert:
    """Insert and return a sample alert."""
    alert = Alert(
        threat_type="ddos",
        severity="high",
        confidence=0.85,
        src_ip="10.0.0.1",
        dst_ip="192.168.1.1",
        src_port=12345,
        dst_port=80,
        protocol="TCP",
        detector_id="ddos-detector-v1",
        schema_version="1.0",
        sensor_source="sensor-alpha",
        evidence=[],
        status="new",
    )
    db_session.add(alert)
    await db_session.flush()
    await db_session.refresh(alert)
    return alert
