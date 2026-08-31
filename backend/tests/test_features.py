import pytest
import pytest_asyncio
import uuid

from app.core.config import REDIS_URL
from app.services.state.redis_client import RedisStateService
from app.services.features.state import FeatureStateAdapter
from app.services.features.engine import FeatureEngine
from app.services.streaming.consumer import ConsumerMessage
from app.schemas.canonical import CanonicalEvent, EventType
from app.schemas.features import (
    FeatureMechanism, FeatureRecord, DetectorDomain, EntityType,
    WindowType, DnsFeatureRecord, TlsC2FeatureRecord, ReconFeatureRecord,
    CorrelationStatus
)
from app.services.features.keys import build_entity_key

@pytest_asyncio.fixture
async def redis_service():
    """Provides a started RedisStateService for integration testing."""
    service = RedisStateService(REDIS_URL)
    await service.start()
    yield service
    await service.stop()

@pytest.fixture
def state_adapter(redis_service):
    return FeatureStateAdapter(redis_service)

@pytest.fixture
def engine(state_adapter):
    return FeatureEngine(state_adapter)

@pytest.mark.asyncio
async def test_canonical_normalization_connection(engine):
    msg = ConsumerMessage(
        topic="irochi.events.connection.v1",
        partition=0,
        offset=1,
        key=None,
        payload={
            "event_id": str(uuid.uuid4()),
            "event_type": "connection",
            "connection_id": "test_conn_1",
            "timestamp": 1234567890000000,
            "timestamp_precision": "microsecond",
            "ingest_timestamp": 1234567891000000,
            "sensor_source": "zeek",
            "src_ip": "1.1.1.1",
            "dst_ip": "2.2.2.2",
            "src_port": 12345,
            "dst_port": 80,
            "protocol": "tcp",
            "schema_version": "1.0",
            "payload": {
                "duration": 5.0
            }
        }
    )
    event = engine.parse_canonical_event(msg)
    assert event is not None
    assert event.event_type == EventType.CONNECTION
    assert event.src_ip == "1.1.1.1"

@pytest.mark.asyncio
async def test_canonical_normalization_dns(engine):
    msg = ConsumerMessage(
        topic="irochi.events.dns.v1",
        partition=0,
        offset=1,
        key=None,
        payload={
            "event_id": str(uuid.uuid4()),
            "event_type": "dns",
            "connection_id": "test_conn_2",
            "timestamp": 1234567890000000,
            "timestamp_precision": "microsecond",
            "ingest_timestamp": 1234567891000000,
            "sensor_source": "zeek",
            "src_ip": "1.1.1.1",
            "dst_ip": "8.8.8.8",
            "src_port": 12345,
            "dst_port": 53,
            "protocol": "udp",
            "schema_version": "1.0",
            "payload": {
                "query": "evil.com",
                "qtype_name": "A"
            }
        }
    )
    event = engine.parse_canonical_event(msg)
    assert event is not None
    assert event.event_type == EventType.DNS
    assert event.payload.query == "evil.com"

@pytest.mark.asyncio
async def test_canonical_normalization_tls(engine):
    msg = ConsumerMessage(
        topic="irochi.events.tls.v1",
        partition=0,
        offset=1,
        key=None,
        payload={
            "event_id": str(uuid.uuid4()),
            "event_type": "tls",
            "connection_id": "test_conn_3",
            "timestamp": 1234567890000000,
            "timestamp_precision": "microsecond",
            "ingest_timestamp": 1234567891000000,
            "sensor_source": "zeek",
            "src_ip": "1.1.1.1",
            "dst_ip": "2.2.2.2",
            "protocol": "tcp",
            "schema_version": "1.0",
            "payload": {
                "ja3": "mock_ja3",
                "server_name": "evil.com"
            }
        }
    )
    event = engine.parse_canonical_event(msg)
    assert event is not None
    assert event.event_type == EventType.TLS
    assert event.payload.ja3 == "mock_ja3"

@pytest.mark.asyncio
async def test_invalid_canonical_event(engine):
    msg = ConsumerMessage(
        topic="irochi.events.connection.v1",
        partition=0,
        offset=1,
        key=None,
        payload={
            # Missing required fields
            "event_type": "connection",
        }
    )
    event = engine.parse_canonical_event(msg)
    assert event is None

@pytest.mark.asyncio
async def test_entity_extraction():
    # Valid extractions
    assert build_entity_key(EntityType.SOURCE, "1.1.1.1", "2.2.2.2", "conn_1") == "1.1.1.1"
    assert build_entity_key(EntityType.DESTINATION, "1.1.1.1", "2.2.2.2", "conn_1") == "2.2.2.2"
    assert build_entity_key(EntityType.PAIR, "1.1.1.1", "2.2.2.2", "conn_1") == "1.1.1.1|2.2.2.2"
    assert build_entity_key(EntityType.CONNECTION, "1.1.1.1", "2.2.2.2", "conn_1") == "conn_1"

    # Invalid (missing context)
    with pytest.raises(ValueError):
        build_entity_key(EntityType.SOURCE, "", "2.2.2.2", "conn_1")
    with pytest.raises(ValueError):
        build_entity_key(EntityType.CONNECTION, "1.1.1.1", "2.2.2.2", "")

@pytest.mark.asyncio
async def test_enrichment_mechanism_dns(engine):
    msg = ConsumerMessage(
        topic="irochi.events.dns.v1",
        partition=0,
        offset=1,
        key=None,
        payload={
            "event_id": str(uuid.uuid4()),
            "event_type": "dns",
            "connection_id": "conn_enrich",
            "timestamp": 1234567890000000,
            "timestamp_precision": "microsecond",
            "ingest_timestamp": 1234567891000000,
            "sensor_source": "zeek",
            "src_ip": "10.0.0.1",
            "dst_ip": "8.8.8.8",
            "protocol": "udp",
            "schema_version": "1.0",
            "payload": {
                "query": "www.example.com",
                "qtype_name": "A"
            }
        }
    )
    records = await engine.process(msg)
    assert len(records) > 0

    # Find enrichment record
    enrich_records = [r for r in records if r.mechanism == FeatureMechanism.ENRICHMENT]
    assert len(enrich_records) == 1

    record = enrich_records[0]
    assert isinstance(record, DnsFeatureRecord)
    assert record.entity_type == EntityType.SOURCE
    assert record.entity_key == "10.0.0.1"
    assert record.window_type is None
    assert record.window_start is None
    assert record.window_end is None
    assert record.payload.query_length == 15
    assert record.payload.label_count == 3
    assert record.payload.max_label_length == 7
    assert record.provenance["source_events"] == [msg.payload["event_id"]]

@pytest.mark.asyncio
async def test_sliding_mechanism_dns(engine, redis_service):
    await redis_service._client.flushdb()

    msg = ConsumerMessage(
        topic="irochi.events.dns.v1",
        partition=0,
        offset=1,
        key=None,
        payload={
            "event_id": str(uuid.uuid4()),
            "event_type": "dns",
            "connection_id": "conn_slide",
            "timestamp": 1000000000000000,
            "timestamp_precision": "microsecond",
            "ingest_timestamp": 1000000000000000,
            "sensor_source": "zeek",
            "src_ip": "10.0.0.2",
            "dst_ip": "8.8.8.8",
            "protocol": "udp",
            "schema_version": "1.0",
            "payload": {
                "query": "slide.com",
                "qtype_name": "A"
            }
        }
    )
    records = await engine.process(msg)

    slide_records = [r for r in records if r.mechanism == FeatureMechanism.WINDOWED]
    assert len(slide_records) == 1

    record = slide_records[0]
    assert record.entity_type == EntityType.SOURCE
    assert record.entity_key == "10.0.0.2"
    assert record.window_type == WindowType.SLIDING
    assert record.payload.query_frequency > 0

@pytest.mark.asyncio
async def test_tumbling_mechanism_recon(engine, redis_service):
    await redis_service._client.flushdb()

    msg1 = ConsumerMessage(
        topic="irochi.events.connection.v1",
        partition=0,
        offset=1,
        key=None,
        payload={
            "event_id": str(uuid.uuid4()),
            "event_type": "connection",
            "connection_id": "conn_tumb1",
            "timestamp": 1000000000000000,
            "timestamp_precision": "microsecond",
            "ingest_timestamp": 1000000000000000,
            "sensor_source": "zeek",
            "src_ip": "10.0.0.3",
            "dst_ip": "2.2.2.2",
            "src_port": 1000,
            "dst_port": 80,
            "protocol": "tcp",
            "schema_version": "1.0",
            "payload": {}
        }
    )
    msg2 = ConsumerMessage(
        topic="irochi.events.connection.v1",
        partition=0,
        offset=2,
        key=None,
        payload={
            "event_id": str(uuid.uuid4()),
            "event_type": "connection",
            "connection_id": "conn_tumb2",
            "timestamp": 1000000000000000,
            "timestamp_precision": "microsecond",
            "ingest_timestamp": 1000000000000000,
            "sensor_source": "zeek",
            "src_ip": "10.0.0.3",
            "dst_ip": "2.2.2.2",
            "src_port": 1000,
            "dst_port": 443,
            "protocol": "tcp",
            "schema_version": "1.0",
            "payload": {}
        }
    )
    await engine.process(msg1)
    records = await engine.process(msg2)

    tumb_records = [r for r in records if r.mechanism == FeatureMechanism.WINDOWED and r.detector_domain == DetectorDomain.RECON]
    assert len(tumb_records) == 1

    record = tumb_records[0]
    assert record.window_type == WindowType.TUMBLING
    assert record.payload.unique_destination_ports == 2

@pytest.mark.asyncio
async def test_correlation_mechanism(engine, redis_service):
    await redis_service._client.flushdb()

    conn_id = "corr_test_1"

    msg_conn = ConsumerMessage(
        topic="irochi.events.connection.v1",
        partition=0,
        offset=1,
        key=None,
        payload={
            "event_id": str(uuid.uuid4()),
            "event_type": "connection",
            "connection_id": conn_id,
            "timestamp": 1000000000000000,
            "timestamp_precision": "microsecond",
            "ingest_timestamp": 1000000000000000,
            "sensor_source": "zeek",
            "src_ip": "10.0.0.4",
            "dst_ip": "2.2.2.2",
            "protocol": "tcp",
            "schema_version": "1.0",
            "payload": {}
        }
    )
    records1 = await engine.process(msg_conn)
    corr_records1 = [r for r in records1 if r.mechanism == FeatureMechanism.CORRELATION]
    assert len(corr_records1) == 1
    assert corr_records1[0].payload.correlation_status == CorrelationStatus.PARTIAL

    msg_tls = ConsumerMessage(
        topic="irochi.events.tls.v1",
        partition=0,
        offset=2,
        key=None,
        payload={
            "event_id": str(uuid.uuid4()),
            "event_type": "tls",
            "connection_id": conn_id,
            "timestamp": 1000000000000000,
            "timestamp_precision": "microsecond",
            "ingest_timestamp": 1000000000000000,
            "sensor_source": "zeek",
            "src_ip": "10.0.0.4",
            "dst_ip": "2.2.2.2",
            "protocol": "tcp",
            "schema_version": "1.0",
            "payload": {}
        }
    )
    records2 = await engine.process(msg_tls)
    corr_records2 = [r for r in records2 if r.mechanism == FeatureMechanism.CORRELATION]
    assert len(corr_records2) == 1
    assert corr_records2[0].payload.correlation_status == CorrelationStatus.COMPLETE

@pytest.mark.asyncio
async def test_revision_monotonicity(engine, redis_service):
    await redis_service._client.flushdb()

    msg1 = ConsumerMessage(
        topic="irochi.events.dns.v1",
        partition=0,
        offset=1,
        key=None,
        payload={
            "event_id": str(uuid.uuid4()),
            "event_type": "dns",
            "connection_id": "conn_rev",
            "timestamp": 1000000000000000,
            "timestamp_precision": "microsecond",
            "ingest_timestamp": 1000000000000000,
            "sensor_source": "zeek",
            "src_ip": "10.0.0.5",
            "dst_ip": "8.8.8.8",
            "protocol": "udp",
            "schema_version": "1.0",
            "payload": {
                "query": "rev1.com",
                "qtype_name": "A"
            }
        }
    )
    records1 = await engine.process(msg1)
    enrich1 = [r for r in records1 if r.mechanism == FeatureMechanism.ENRICHMENT][0]

    msg2 = ConsumerMessage(
        topic="irochi.events.dns.v1",
        partition=0,
        offset=2,
        key=None,
        payload={
            "event_id": str(uuid.uuid4()),
            "event_type": "dns",
            "connection_id": "conn_rev2",
            "timestamp": 1000000000000000,
            "timestamp_precision": "microsecond",
            "ingest_timestamp": 1000000000000000,
            "sensor_source": "zeek",
            "src_ip": "10.0.0.5",
            "dst_ip": "8.8.8.8",
            "protocol": "udp",
            "schema_version": "1.0",
            "payload": {
                "query": "rev2.com",
                "qtype_name": "A"
            }
        }
    )
    records2 = await engine.process(msg2)
    enrich2 = [r for r in records2 if r.mechanism == FeatureMechanism.ENRICHMENT][0]

    assert enrich2.revision > enrich1.revision
