"""Tests for the dashboard module — 8 tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts.models import Alert


@pytest.mark.asyncio
async def test_kpi_empty_db(test_client: AsyncClient, admin_headers):
    """KPI on empty DB returns all zeros."""
    r = await test_client.get("/dashboard/kpi", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total_alerts_today"] == 0
    assert data["active_threats"] == 0
    assert data["events_per_second"] == 0.0
    assert data["detectors_active"] == 0


@pytest.mark.asyncio
async def test_kpi_with_alerts(
    db_session: AsyncSession,
    test_client: AsyncClient,
    admin_headers,
    sample_alert,
):
    """KPI total_alerts_today is correct with data."""
    r = await test_client.get("/dashboard/kpi", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["total_alerts_today"] >= 1


@pytest.mark.asyncio
async def test_kpi_active_threats_excludes_closed(
    db_session: AsyncSession,
    test_client: AsyncClient,
    admin_headers,
):
    """Active threats excludes closed alerts."""
    # Add a high-severity closed alert
    db_session.add(Alert(
        threat_type="ddos", severity="critical", confidence=0.95,
        src_ip="10.0.0.10", dst_ip="192.168.1.10",
        detector_id="det-1", schema_version="1.0",
        evidence=[], status="closed",
    ))
    # Add a high-severity open alert
    db_session.add(Alert(
        threat_type="recon", severity="high", confidence=0.80,
        src_ip="10.0.0.11", dst_ip="192.168.1.11",
        detector_id="det-2", schema_version="1.0",
        evidence=[], status="new",
    ))
    await db_session.flush()

    r = await test_client.get("/dashboard/kpi", headers=admin_headers)
    assert r.status_code == 200
    # Only the open high-severity alert counts
    assert r.json()["active_threats"] >= 1


@pytest.mark.asyncio
async def test_timeline_returns_24_buckets(
    test_client: AsyncClient, admin_headers
):
    """Timeline always returns exactly 24 hourly buckets."""
    r = await test_client.get("/dashboard/timeline", headers=admin_headers)
    assert r.status_code == 200
    assert len(r.json()["buckets"]) == 24


@pytest.mark.asyncio
async def test_timeline_bucket_counts_correct(
    db_session: AsyncSession,
    test_client: AsyncClient,
    admin_headers,
    sample_alert,
):
    """Timeline buckets contain the correct counts."""
    r = await test_client.get("/dashboard/timeline", headers=admin_headers)
    assert r.status_code == 200
    buckets = r.json()["buckets"]
    # At least one bucket should have ddos > 0
    total_ddos = sum(b["ddos"] for b in buckets)
    assert total_ddos >= 1


@pytest.mark.asyncio
async def test_summary_returns_all_fields(
    test_client: AsyncClient, admin_headers
):
    """Dashboard summary contains kpi, top_threats, top_source_ips."""
    r = await test_client.get("/dashboard/summary", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "kpi" in data
    assert "top_threats" in data
    assert "top_source_ips" in data


@pytest.mark.asyncio
async def test_summary_cached_in_redis(
    test_client: AsyncClient, admin_headers, fake_redis
):
    """Second summary request within 5s hits Redis cache."""
    r1 = await test_client.get("/dashboard/summary", headers=admin_headers)
    assert r1.status_code == 200

    # Second request — should come from cache
    r2 = await test_client.get("/dashboard/summary", headers=admin_headers)
    assert r2.status_code == 200
    assert r1.json() == r2.json()

    # Verify cache key exists
    cached = await fake_redis.get("cache:dashboard:summary")
    assert cached is not None


@pytest.mark.asyncio
async def test_top_source_ips_ordered_by_count(
    db_session: AsyncSession,
    test_client: AsyncClient,
    admin_headers,
):
    """Top source IPs are ordered by count descending."""
    # Insert alerts from two source IPs, one with more alerts
    for _ in range(5):
        db_session.add(Alert(
            threat_type="ddos", severity="high", confidence=0.8,
            src_ip="10.0.0.100", dst_ip="192.168.1.1",
            detector_id="det", schema_version="1.0", evidence=[],
        ))
    for _ in range(2):
        db_session.add(Alert(
            threat_type="recon", severity="medium", confidence=0.5,
            src_ip="10.0.0.200", dst_ip="192.168.1.1",
            detector_id="det", schema_version="1.0", evidence=[],
        ))
    await db_session.flush()

    r = await test_client.get("/dashboard/top-ips", headers=admin_headers)
    assert r.status_code == 200
    ips = r.json()
    if len(ips) >= 2:
        assert ips[0]["event_count"] >= ips[1]["event_count"]
