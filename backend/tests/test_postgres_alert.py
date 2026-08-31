import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core import config
from app.models.alert import Alert
from app.models.base import Base
from app.services.postgres_alert_service import PostgresAlertService, StaleUpdateError


@pytest_asyncio.fixture
async def async_session_factory():
    # Create a test URL by replacing the DB name from the config URL
    test_url = config.POSTGRES_URL.rsplit('/', 1)[0] + "/irochi_test"
    engine = create_async_engine(test_url, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    yield SessionLocal

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_session_factory) -> AsyncSession:
    async with async_session_factory() as session:
        yield session


@pytest.mark.asyncio
async def test_create_and_get_alert(db_session: AsyncSession):
    service = PostgresAlertService(db_session)
    alert_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    new_alert = Alert(
        alert_id=alert_id,
        detector_output_id=str(uuid.uuid4()),
        detector_id="ddos_detector",
        threat_type="volumetric_ddos",
        entity_type="destination",
        entity_key="192.168.1.100",
        detected_at=now,
        created_at=now,
        first_seen_at=now,
        last_seen_at=now,
        status="new",
        severity="high",
        severity_candidate="high",
        confidence=0.95,
        score=95.0,
        title="DDoS Attack Detected",
        evidence_summary="High volume traffic to 192.168.1.100",
        evidence={"traffic_rate": "500Gbps"},
        source_feature_references=[{"feature_id": "byte_count", "revision": 1}],
        detector_version="1.0.0",
        model_version=None,
        schema_version="1.0",
        update_count=0
    )

    created = await service.create_alert(new_alert)
    assert created.alert_id == alert_id

    fetched = await service.get_alert(alert_id)
    assert fetched is not None
    assert fetched.entity_type == "destination"
    assert fetched.evidence["traffic_rate"] == "500Gbps"


@pytest.mark.asyncio
async def test_stale_update_error(db_session: AsyncSession):
    service = PostgresAlertService(db_session)
    alert_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    new_alert = Alert(
        alert_id=alert_id,
        detector_output_id="out-123",
        detector_id="recon_detector",
        threat_type="recon_portscan",
        entity_type="source",
        entity_key="10.0.0.5",
        detected_at=now,
        created_at=now,
        first_seen_at=now,
        last_seen_at=now,
        status="new",
        severity="medium",
        severity_candidate="medium",
        confidence=None,
        score=None,
        title="Port Scan",
        evidence_summary="Scanning ports",
        evidence={},
        source_feature_references=[],
        detector_version="1.0.0",
        model_version=None,
        schema_version="1.0",
        update_count=5
    )
    await service.create_alert(new_alert)

    # Try updating with wrong expected_update_count
    with pytest.raises(StaleUpdateError):
        await service.update_alert_fields(
            alert_id=alert_id,
            updates={"status": "investigating"},
            expected_update_count=4  # actual is 5
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("valid_entity_type, valid_entity_key", [
    ("source", "192.168.1.5"),
    ("destination", "10.0.0.1"),
    ("pair", "192.168.1.5<>10.0.0.1"),
    ("connection", "192.168.1.5:44321<>10.0.0.1:443-TCP")
])
async def test_entity_type_constraint_accepts_valid(
    db_session: AsyncSession, valid_entity_type: str, valid_entity_key: str
):
    service = PostgresAlertService(db_session)
    now = datetime.now(timezone.utc)

    new_alert = Alert(
        alert_id=uuid.uuid4(),
        detector_output_id="out-123",
        detector_id="recon_detector",
        threat_type="recon_portscan",
        entity_type=valid_entity_type,
        entity_key=valid_entity_key,
        detected_at=now,
        created_at=now,
        first_seen_at=now,
        last_seen_at=now,
        status="new",
        severity="medium",
        severity_candidate="medium",
        confidence=None,
        score=None,
        title=f"Test {valid_entity_type}",
        evidence_summary="Testing",
        evidence={},
        source_feature_references=[],
        detector_version="1.0.0",
        model_version=None,
        schema_version="1.0",
        update_count=0
    )

    created = await service.create_alert(new_alert)
    assert created.entity_type == valid_entity_type


@pytest.mark.asyncio
async def test_entity_type_constraint_rejects_event(db_session: AsyncSession):
    service = PostgresAlertService(db_session)
    now = datetime.now(timezone.utc)

    new_alert = Alert(
        alert_id=uuid.uuid4(),
        detector_output_id="out-123",
        detector_id="ddos_detector",
        threat_type="volumetric_ddos",
        entity_type="event",  # INVALID!
        entity_key="10.0.0.5",
        detected_at=now,
        created_at=now,
        first_seen_at=now,
        last_seen_at=now,
        status="new",
        severity="medium",
        severity_candidate="medium",
        confidence=None,
        score=None,
        title="Bad Entity",
        evidence_summary="Bad Entity",
        evidence={},
        source_feature_references=[],
        detector_version="1.0.0",
        model_version=None,
        schema_version="1.0",
        update_count=0
    )

    with pytest.raises(IntegrityError):
        await service.create_alert(new_alert)


@pytest.mark.asyncio
async def test_status_constraint_rejects_invalid(db_session: AsyncSession):
    service = PostgresAlertService(db_session)
    now = datetime.now(timezone.utc)

    new_alert = Alert(
        alert_id=uuid.uuid4(),
        detector_output_id="out-123",
        detector_id="ddos_detector",
        threat_type="volumetric_ddos",
        entity_type="source",
        entity_key="10.0.0.5",
        detected_at=now,
        created_at=now,
        first_seen_at=now,
        last_seen_at=now,
        status="open",  # INVALID lifecycle value!
        severity="medium",
        severity_candidate="medium",
        confidence=None,
        score=None,
        title="Bad Status",
        evidence_summary="Bad Status",
        evidence={},
        source_feature_references=[],
        detector_version="1.0.0",
        model_version=None,
        schema_version="1.0",
        update_count=0
    )

    with pytest.raises(IntegrityError):
        await service.create_alert(new_alert)
