"""Tests for the alert engine — 8 tests."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import fakeredis.aioredis
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.alert_engine.engine import (
    assign_severity,
    is_duplicate,
    process_detector_result,
)
from app.alert_engine.schemas import DetectorResult
from app.alerts.models import Alert


# ── Severity assignment tests ────────────────────────────────────


def test_assign_severity_critical():
    """confidence=0.95 → critical."""
    assert assign_severity(0.95) == "critical"


def test_assign_severity_high():
    """confidence=0.75 → high."""
    assert assign_severity(0.75) == "high"


def test_assign_severity_medium():
    """confidence=0.50 → medium."""
    assert assign_severity(0.50) == "medium"


def test_assign_severity_low():
    """confidence=0.10 → low."""
    assert assign_severity(0.10) == "low"


# ── Deduplication tests ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_deduplication_suppresses_duplicate(
    db_session: AsyncSession,
    fake_redis,
):
    """Processing the same DetectorResult twice creates only 1 alert."""
    result = DetectorResult(
        event_id=uuid4(),
        threat_type="ddos",
        detector_id="det-1",
        confidence=0.85,
        evidence=[],
        src_ip="10.0.0.1",
        dst_ip="192.168.1.1",
        schema_version="1.0",
        detected_at=datetime.utcnow(),
    )

    await process_detector_result(db_session, fake_redis, result)

    # Second call with same src/dst/threat — should be deduplicated
    result2 = DetectorResult(
        event_id=uuid4(),
        threat_type="ddos",
        detector_id="det-1",
        confidence=0.90,
        evidence=[],
        src_ip="10.0.0.1",
        dst_ip="192.168.1.1",
        schema_version="1.0",
        detected_at=datetime.utcnow(),
    )
    await process_detector_result(db_session, fake_redis, result2)

    from sqlalchemy import cast
    from sqlalchemy.dialects.postgresql import INET

    count_result = await db_session.execute(
        select(Alert).where(
            Alert.src_ip == cast("10.0.0.1", INET),
            Alert.dst_ip == cast("192.168.1.1", INET),
            Alert.threat_type == "ddos",
        )
    )
    alerts = count_result.scalars().all()
    assert len(alerts) == 1


@pytest.mark.asyncio
async def test_deduplication_allows_after_ttl(
    db_session: AsyncSession,
    fake_redis,
):
    """After deleting the dedup key, a second result creates a new alert."""
    result = DetectorResult(
        event_id=uuid4(),
        threat_type="recon",
        detector_id="det-2",
        confidence=0.60,
        evidence=[],
        src_ip="10.0.0.50",
        dst_ip="192.168.1.50",
        schema_version="1.0",
        detected_at=datetime.utcnow(),
    )

    await process_detector_result(db_session, fake_redis, result)

    # Manually delete the dedup key to simulate TTL expiry
    await fake_redis.delete("dedup:recon:10.0.0.50:192.168.1.50")

    result2 = DetectorResult(
        event_id=uuid4(),
        threat_type="recon",
        detector_id="det-2",
        confidence=0.65,
        evidence=[],
        src_ip="10.0.0.50",
        dst_ip="192.168.1.50",
        schema_version="1.0",
        detected_at=datetime.utcnow(),
    )
    await process_detector_result(db_session, fake_redis, result2)

    from sqlalchemy import cast
    from sqlalchemy.dialects.postgresql import INET
    count_result = await db_session.execute(
        select(Alert).where(
            Alert.src_ip == cast("10.0.0.50", INET),
            Alert.threat_type == "recon",
        )
    )
    alerts = count_result.scalars().all()
    assert len(alerts) == 2


@pytest.mark.asyncio
async def test_commit_failure_does_not_publish(
    db_session: AsyncSession,
    fake_redis,
):
    """If DB commit fails, redis.publish should NOT be called."""
    result = DetectorResult(
        event_id=uuid4(),
        threat_type="dns_dga",
        detector_id="det-3",
        confidence=0.75,
        evidence=[],
        src_ip="10.0.0.99",
        dst_ip="192.168.1.99",
        schema_version="1.0",
        detected_at=datetime.utcnow(),
    )

    publish_spy = AsyncMock()
    original_publish = fake_redis.publish
    fake_redis.publish = publish_spy

    # Mock commit to raise
    with patch.object(db_session, "commit", side_effect=Exception("DB error")):
        await process_detector_result(db_session, fake_redis, result)

    # publish should NOT have been called
    publish_spy.assert_not_called()

    # Restore
    fake_redis.publish = original_publish


@pytest.mark.asyncio
async def test_valid_detector_result_creates_alert(
    db_session: AsyncSession,
    fake_redis,
):
    """Full happy path: DetectorResult → alert in DB → published to Redis."""
    result = DetectorResult(
        event_id=uuid4(),
        threat_type="tls_c2",
        detector_id="det-4",
        confidence=0.92,
        evidence=[],
        src_ip="10.0.0.200",
        dst_ip="192.168.1.200",
        src_port=443,
        dst_port=54321,
        protocol="TCP",
        sensor_source="sensor-beta",
        schema_version="1.0",
        detected_at=datetime.utcnow(),
    )

    await process_detector_result(db_session, fake_redis, result)

    from sqlalchemy import cast
    from sqlalchemy.dialects.postgresql import INET
    # Verify alert in DB
    db_result = await db_session.execute(
        select(Alert).where(Alert.src_ip == cast("10.0.0.200", INET))
    )
    alert = db_result.scalar_one_or_none()
    assert alert is not None
    assert alert.threat_type == "tls_c2"
    assert alert.severity == "critical"  # 0.92 >= 0.90
    assert alert.detector_id == "det-4"
    assert alert.protocol == "TCP"
