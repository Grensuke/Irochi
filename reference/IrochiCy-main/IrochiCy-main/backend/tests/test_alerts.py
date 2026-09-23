"""Tests for the alerts module — 15 tests."""

from __future__ import annotations

import csv
import io

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts.models import Alert, AlertStatusHistory


@pytest.mark.asyncio
async def test_list_alerts_empty(test_client: AsyncClient, admin_headers):
    """Empty DB returns no alerts."""
    r = await test_client.get("/alerts/", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_alerts_with_data(
    test_client: AsyncClient, admin_headers, sample_alert
):
    """List alerts returns correct total when data exists."""
    r = await test_client.get("/alerts/", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["total"] >= 1


@pytest.mark.asyncio
async def test_list_alerts_filter_severity(
    test_client: AsyncClient, admin_headers, sample_alert
):
    """Filter by severity=high returns the sample alert."""
    r = await test_client.get(
        "/alerts/?severity=high", headers=admin_headers
    )
    assert r.status_code == 200
    assert all(a["severity"] == "high" for a in r.json()["items"])


@pytest.mark.asyncio
async def test_list_alerts_filter_threat_type(
    test_client: AsyncClient, admin_headers, sample_alert
):
    """Filter by threat_type=ddos returns matching alerts."""
    r = await test_client.get(
        "/alerts/?threat_type=ddos", headers=admin_headers
    )
    assert r.status_code == 200
    assert all(a["threat_type"] == "ddos" for a in r.json()["items"])


@pytest.mark.asyncio
async def test_list_alerts_filter_status(
    test_client: AsyncClient, admin_headers, sample_alert
):
    """Filter by status=new returns matching alerts."""
    r = await test_client.get(
        "/alerts/?status=new", headers=admin_headers
    )
    assert r.status_code == 200
    assert all(a["status"] == "new" for a in r.json()["items"])


@pytest.mark.asyncio
async def test_list_alerts_search_src_ip(
    test_client: AsyncClient, admin_headers, sample_alert
):
    """Search by partial src_ip matches."""
    r = await test_client.get(
        "/alerts/?search=10.0.0", headers=admin_headers
    )
    assert r.status_code == 200
    assert r.json()["total"] >= 1


@pytest.mark.asyncio
async def test_list_alerts_pagination_page2(
    db_session: AsyncSession,
    test_client: AsyncClient,
    admin_headers,
):
    """Page 2 with page_size=1 returns the second alert."""
    for i in range(3):
        db_session.add(Alert(
            threat_type="recon",
            severity="low",
            confidence=0.3,
            src_ip=f"10.0.0.{i+1}",
            dst_ip="192.168.1.1",
            detector_id="recon-det",
            schema_version="1.0",
            evidence=[],
        ))
    await db_session.flush()

    r = await test_client.get(
        "/alerts/?page=2&page_size=1", headers=admin_headers
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) == 1
    assert data["page"] == 2
    assert data["has_next"] is True


@pytest.mark.asyncio
async def test_list_alerts_page_size_clamped_to_100(
    test_client: AsyncClient, admin_headers
):
    """page_size > 100 is rejected by validation."""
    r = await test_client.get(
        "/alerts/?page_size=200", headers=admin_headers
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_get_alert_detail(
    test_client: AsyncClient, admin_headers, sample_alert
):
    """Get a specific alert returns full AlertResponse."""
    r = await test_client.get(
        f"/alerts/{sample_alert.id}", headers=admin_headers
    )
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == str(sample_alert.id)
    assert data["threat_type"] == "ddos"
    assert data["severity"] == "high"


@pytest.mark.asyncio
async def test_get_alert_not_found(
    test_client: AsyncClient, admin_headers
):
    """Get a nonexistent alert returns 404."""
    r = await test_client.get(
        "/alerts/00000000-0000-0000-0000-000000000000",
        headers=admin_headers,
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_status_new_to_acknowledged(
    test_client: AsyncClient, admin_headers, sample_alert
):
    """Transition new → acknowledged succeeds."""
    r = await test_client.patch(
        f"/alerts/{sample_alert.id}/status",
        json={"status": "acknowledged"},
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "acknowledged"


@pytest.mark.asyncio
async def test_update_status_invalid_transition(
    db_session: AsyncSession,
    test_client: AsyncClient,
    admin_headers,
):
    """Transition closed → acknowledged returns 409."""
    alert = Alert(
        threat_type="recon",
        severity="medium",
        confidence=0.6,
        src_ip="10.0.0.5",
        dst_ip="192.168.1.5",
        detector_id="recon-det",
        schema_version="1.0",
        evidence=[],
        status="closed",
    )
    db_session.add(alert)
    await db_session.flush()
    await db_session.refresh(alert)

    r = await test_client.patch(
        f"/alerts/{alert.id}/status",
        json={"status": "acknowledged"},
        headers=admin_headers,
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_update_status_with_note(
    test_client: AsyncClient, admin_headers, sample_alert
):
    """Status update with a note appends to analyst_notes."""
    r = await test_client.patch(
        f"/alerts/{sample_alert.id}/status",
        json={"status": "investigating", "note": "Checking packet captures"},
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert "Checking packet captures" in r.json()["analyst_notes"]


@pytest.mark.asyncio
async def test_update_status_history_written(
    db_session: AsyncSession,
    test_client: AsyncClient,
    admin_headers,
    sample_alert,
):
    """Status update writes to alert_status_history table."""
    await test_client.patch(
        f"/alerts/{sample_alert.id}/status",
        json={"status": "acknowledged"},
        headers=admin_headers,
    )

    result = await db_session.execute(
        select(AlertStatusHistory).where(
            AlertStatusHistory.alert_id == sample_alert.id
        )
    )
    history = result.scalars().all()
    assert len(history) >= 1
    assert history[0].old_status == "new"
    assert history[0].new_status == "acknowledged"


@pytest.mark.asyncio
async def test_export_csv(
    test_client: AsyncClient, admin_headers, sample_alert
):
    """CSV export returns valid CSV with correct headers."""
    r = await test_client.get("/alerts/export/csv", headers=admin_headers)
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert "attachment" in r.headers.get("content-disposition", "")

    reader = csv.reader(io.StringIO(r.text))
    rows = list(reader)
    assert rows[0] == [
        "id", "threat_type", "severity", "confidence",
        "src_ip", "dst_ip", "src_port", "dst_port",
        "protocol", "status", "created_at",
    ]
    assert len(rows) >= 2  # header + at least 1 data row
