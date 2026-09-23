import asyncio
import json
import random
from uuid import uuid4

import asyncpg
import httpx
import pytest
from aiokafka import AIOKafkaProducer

from app.config import settings
from tests.e2e.helpers import build_detector_result, poll_for_alert

pytestmark = pytest.mark.e2e


@pytest.fixture
async def raw_db():
    dsn = settings.database_url.replace("+asyncpg", "")
    conn = await asyncpg.connect(dsn=dsn)
    yield conn
    await conn.close()


@pytest.mark.asyncio
async def test_alert_status_history_written_on_every_transition(
    live_client: httpx.AsyncClient,
    admin_headers: dict,
    redpanda_producer: AIOKafkaProducer,
    raw_db: asyncpg.Connection,
):
    """Every status change must produce a row in alert_status_history."""
    src_ip = f"10.0.99.{random.randint(1, 254)}"
    payload = build_detector_result(threat_type="recon", src_ip=src_ip, confidence=0.7)
    await redpanda_producer.send_and_wait("detector.results", json.dumps(payload).encode())
    
    alert = await poll_for_alert(live_client, admin_headers, src_ip, "recon")
    alert_id = alert["id"]
    
    await live_client.patch(f"/alerts/{alert_id}/status", json={"status": "acknowledged"}, headers=admin_headers)
    await live_client.patch(f"/alerts/{alert_id}/status", json={"status": "investigating"}, headers=admin_headers)
    await live_client.patch(f"/alerts/{alert_id}/status", json={"status": "closed"}, headers=admin_headers)
    
    # Query directly
    rows = await raw_db.fetch("SELECT * FROM alert_status_history WHERE alert_id = $1 ORDER BY changed_at ASC", alert_id)
    assert len(rows) == 3
    
    assert rows[0]["new_status"] == "acknowledged"
    assert rows[0]["old_status"] in (None, "new")
    
    assert rows[1]["old_status"] == "acknowledged"
    assert rows[1]["new_status"] == "investigating"
    
    assert rows[2]["old_status"] == "investigating"
    assert rows[2]["new_status"] == "closed"


@pytest.mark.asyncio
async def test_audit_log_written_on_login(live_client: httpx.AsyncClient, raw_db: asyncpg.Connection):
    """Every login must produce a row in audit_log."""
    import datetime
    now = datetime.datetime.utcnow() - datetime.timedelta(seconds=5)
    
    resp = await live_client.post(
        "/auth/login",
        json={"username": settings.initial_admin_username, "password": settings.initial_admin_password},
    )
    assert resp.status_code == 200
    
    rows = await raw_db.fetch("SELECT * FROM audit_log WHERE action='login' AND created_at > $1", now)
    assert len(rows) >= 1
    assert rows[-1]["user_id"] is not None
    assert rows[-1]["ip_address"] is not None


@pytest.mark.asyncio
async def test_alert_constraints_reject_invalid_data(raw_db: asyncpg.Connection):
    """Database constraints must reject out-of-range or invalid values."""
    base_insert = """
        INSERT INTO alerts (id, threat_type, severity, confidence, src_ip, dst_ip, detector_id, schema_version, evidence, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    """
    valid_args = [str(uuid4()), "ddos", "high", 0.9, "10.0.0.1", "192.168.1.1", "d1", "1.0", "[]", "new"]
    
    # Case 1: confidence = 1.5
    args1 = list(valid_args)
    args1[0] = str(uuid4())
    args1[3] = 1.5
    with pytest.raises(asyncpg.CheckViolationError):
        await raw_db.execute(base_insert, *args1)
        
    # Case 2: invalid threat_type
    args2 = list(valid_args)
    args2[0] = str(uuid4())
    args2[1] = "unknown_threat"
    with pytest.raises(asyncpg.CheckViolationError):
        await raw_db.execute(base_insert, *args2)
        
    # Case 3: invalid severity
    args3 = list(valid_args)
    args3[0] = str(uuid4())
    args3[2] = "ultra"
    with pytest.raises(asyncpg.CheckViolationError):
        await raw_db.execute(base_insert, *args3)
        
    # Case 4: invalid status
    args4 = list(valid_args)
    args4[0] = str(uuid4())
    args4[9] = "resolved"
    with pytest.raises(asyncpg.CheckViolationError):
        await raw_db.execute(base_insert, *args4)


@pytest.mark.asyncio
async def test_updated_at_trigger_fires(
    live_client: httpx.AsyncClient, admin_headers: dict, redpanda_producer: AIOKafkaProducer, raw_db: asyncpg.Connection
):
    """updated_at must change automatically when a record is updated."""
    src_ip = f"10.0.98.{random.randint(1, 254)}"
    payload = build_detector_result("dns_dga", src_ip, 0.6)
    await redpanda_producer.send_and_wait("detector.results", json.dumps(payload).encode())
    
    alert = await poll_for_alert(live_client, admin_headers, src_ip, "dns_dga")
    alert_id = alert["id"]
    
    orig_updated = await raw_db.fetchval("SELECT updated_at FROM alerts WHERE id = $1", alert_id)
    
    await asyncio.sleep(0.5)
    
    await live_client.patch(f"/alerts/{alert_id}/status", json={"status": "acknowledged"}, headers=admin_headers)
    
    new_updated = await raw_db.fetchval("SELECT updated_at FROM alerts WHERE id = $1", alert_id)
    
    assert new_updated > orig_updated


@pytest.mark.asyncio
async def test_soft_delete_user_not_hard_deleted(live_client: httpx.AsyncClient, admin_headers: dict, raw_db: asyncpg.Connection):
    """DELETE /users/{id} must set is_active=False, NOT remove the row."""
    username = f"e2e_del_{uuid4().hex[:8]}"
    resp = await live_client.post(
        "/users/",
        json={"username": username, "password": "ValidPassword123!", "email": f"{username}@a.com", "full_name": "X", "role": "analyst"},
        headers=admin_headers,
    )
    user_id = resp.json()["id"]
    
    await live_client.delete(f"/users/{user_id}", headers=admin_headers)
    
    row = await raw_db.fetchrow("SELECT is_active, username FROM users WHERE id = $1", user_id)
    assert row is not None
    assert row["is_active"] is False
    assert row["username"] == username


@pytest.mark.asyncio
async def test_assigned_to_null_on_user_deactivation(
    live_client: httpx.AsyncClient, admin_headers: dict, raw_db: asyncpg.Connection, redpanda_producer: AIOKafkaProducer
):
    """ON DELETE SET NULL verification."""
    # Note: We soft delete users via API, but the db level ON DELETE SET NULL is for actual DB deletes.
    # We will test the soft delete logic or hard delete logic. Since /users/{id} soft deletes, it might NOT nullify assigned_to automatically unless there's a trigger, or maybe the spec meant an actual DELETE.
    # Let's perform an actual DB DELETE to test the foreign key ON DELETE SET NULL constraint.
    username = f"e2e_del2_{uuid4().hex[:8]}"
    resp = await live_client.post(
        "/users/",
        json={"username": username, "password": "ValidPassword123!", "email": f"{username}@a.com", "full_name": "X", "role": "analyst"},
        headers=admin_headers,
    )
    user_id = resp.json()["id"]
    
    src_ip = f"10.0.97.{random.randint(1, 254)}"
    payload = build_detector_result("tls_c2", src_ip, 0.95)
    await redpanda_producer.send_and_wait("detector.results", json.dumps(payload).encode())
    alert = await poll_for_alert(live_client, admin_headers, src_ip, "tls_c2")
    alert_id = alert["id"]
    
    await raw_db.execute("UPDATE alerts SET assigned_to = $1 WHERE id = $2", user_id, alert_id)
    
    # HARD delete the user to test the foreign key
    await raw_db.execute("DELETE FROM users WHERE id = $1", user_id)
    
    assigned_to = await raw_db.fetchval("SELECT assigned_to FROM alerts WHERE id = $1", alert_id)
    assert assigned_to is None
