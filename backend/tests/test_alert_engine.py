import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from app.schemas.detectors import DetectorOutput, Decision, SourceFeatureReference
from app.schemas.alerts import Severity
from app.services.alert_engine import AlertEngine
from app.services.postgres_alert_service import PostgresAlertService
from app.services.redis_pubsub import RedisPubSubService


@pytest.fixture
def mock_postgres():
    svc = AsyncMock(spec=PostgresAlertService)
    svc.get_open_alert_by_identity.return_value = None

    # Mock create_alert to return a fake ORM object
    fake_alert = MagicMock()
    fake_alert.alert_id = "test-uuid"
    fake_alert.last_seen_at = datetime.now(timezone.utc)
    fake_alert.threat_type = "test_threat"
    fake_alert.detector_id = "test_detector"
    fake_alert.severity = "high"
    fake_alert.confidence = 0.9
    fake_alert.evidence_summary = {}
    fake_alert.status = "new"
    fake_alert.entity_type = "source"
    fake_alert.entity_key = "1.2.3.4"

    svc.create_alert.return_value = fake_alert
    svc.update_alert_fields.return_value = fake_alert
    return svc


@pytest.fixture
def mock_redis():
    svc = AsyncMock(spec=RedisPubSubService)
    return svc


@pytest.fixture
def alert_engine(mock_postgres, mock_redis):
    return AlertEngine(postgres_service=mock_postgres, redis_service=mock_redis)


@pytest.mark.asyncio
async def test_no_threat_filtered(alert_engine, mock_postgres):
    output = DetectorOutput(
        output_id="out-1",
        input_id="in-1",
        detector_id="ddos_detector",
        threat_type="volumetric_ddos",
        decision=Decision.NO_THREAT,
        evidence={},
        entity_type="source",
        entity_key="1.2.3.4",
        evaluated_at=1234567890,
        detector_version="1.0",
        source_feature_references=[]
    )
    result = await alert_engine.process_detector_output(output)
    assert result is None
    mock_postgres.create_alert.assert_not_called()
    mock_postgres.update_alert_fields.assert_not_called()


@pytest.mark.asyncio
async def test_insufficient_data_filtered(alert_engine, mock_postgres):
    output = DetectorOutput(
        output_id="out-2",
        input_id="in-2",
        detector_id="ddos_detector",
        threat_type="volumetric_ddos",
        decision=Decision.INSUFFICIENT_DATA,
        evidence={},
        entity_type="source",
        entity_key="1.2.3.4",
        evaluated_at=1234567890,
        detector_version="1.0",
        source_feature_references=[]
    )
    result = await alert_engine.process_detector_output(output)
    assert result is None
    mock_postgres.create_alert.assert_not_called()


@pytest.mark.asyncio
async def test_invalid_input_logged_and_filtered(alert_engine, mock_postgres, caplog):
    output = DetectorOutput(
        output_id="out-3",
        input_id="in-3",
        detector_id="ddos_detector",
        threat_type="volumetric_ddos",
        decision=Decision.INVALID_INPUT,
        evidence={"error": "bad packet"},
        entity_type="source",
        entity_key="1.2.3.4",
        evaluated_at=1234567890,
        detector_version="1.0",
        source_feature_references=[]
    )
    result = await alert_engine.process_detector_output(output)
    assert result is None
    mock_postgres.create_alert.assert_not_called()
    assert "Operational error in detector_output" in caplog.text


@pytest.mark.asyncio
async def test_detector_error_logged_and_filtered(alert_engine, mock_postgres, caplog):
    output = DetectorOutput(
        output_id="out-4",
        input_id="in-4",
        detector_id="ddos_detector",
        threat_type="volumetric_ddos",
        decision=Decision.DETECTOR_ERROR,
        evidence={"exception": "timeout"},
        entity_type="source",
        entity_key="1.2.3.4",
        evaluated_at=1234567890,
        detector_version="1.0",
        source_feature_references=[]
    )
    result = await alert_engine.process_detector_output(output)
    assert result is None
    mock_postgres.create_alert.assert_not_called()
    assert "Operational error in detector_output" in caplog.text


@pytest.mark.asyncio
async def test_medium_fallback(alert_engine, mock_postgres):
    output = DetectorOutput(
        output_id="out-5",
        input_id="in-5",
        detector_id="ddos_detector",
        threat_type="volumetric_ddos",
        decision=Decision.DETECTION,
        evidence={},
        entity_type="source",
        entity_key="1.2.3.4",
        evaluated_at=1234567890,
        detector_version="1.0",
        source_feature_references=[]
    )
    await alert_engine.process_detector_output(output)
    mock_postgres.create_alert.assert_called_once()
    args, kwargs = mock_postgres.create_alert.call_args
    assert args[0].severity == Severity.MEDIUM.value


@pytest.mark.asyncio
async def test_four_field_deduplication_identity_update(alert_engine, mock_postgres):
    # Mock that we found an existing alert matching the identity
    existing_alert = MagicMock()
    existing_alert.alert_id = "existing-uuid"
    existing_alert.evidence = {"old": "data"}
    mock_postgres.get_open_alert_by_identity.return_value = existing_alert

    output = DetectorOutput(
        output_id="out-6",
        input_id="in-6",
        detector_id="ddos_detector",
        threat_type="volumetric_ddos",
        decision=Decision.DETECTION,
        evidence={"new": "data"},
        entity_type="source",
        entity_key="1.2.3.4",
        severity_candidate=Severity.HIGH.value,
        evaluated_at=1234567890,
        detector_version="1.0",
        source_feature_references=[]
    )
    await alert_engine.process_detector_output(output)

    mock_postgres.get_open_alert_by_identity.assert_called_once_with(
        detector_id="ddos_detector",
        threat_type="volumetric_ddos",
        entity_type="source",
        entity_key="1.2.3.4"
    )
    mock_postgres.create_alert.assert_not_called()
    mock_postgres.update_alert_fields.assert_called_once()

    args, kwargs = mock_postgres.update_alert_fields.call_args
    assert kwargs["alert_id"] == "existing-uuid"
    assert kwargs["expected_update_count"] == existing_alert.update_count
    updates = kwargs["updates"]
    assert updates["severity"] == Severity.HIGH.value
    assert updates["evidence"] == {"old": "data", "new": "data"}


@pytest.mark.asyncio
async def test_different_identity_creates_new_alert(alert_engine, mock_postgres):
    mock_postgres.get_open_alert_by_identity.return_value = None

    output = DetectorOutput(
        output_id="out-7",
        input_id="in-7",
        detector_id="ddos_detector",
        threat_type="volumetric_ddos",
        decision=Decision.DETECTION,
        evidence={"new": "data"},
        entity_type="source",
        entity_key="1.2.3.4",
        evaluated_at=1234567890,
        detector_version="1.0",
        source_feature_references=[]
    )
    await alert_engine.process_detector_output(output)

    mock_postgres.get_open_alert_by_identity.assert_called_once()
    mock_postgres.create_alert.assert_called_once()
    mock_postgres.update_alert_fields.assert_not_called()


@pytest.mark.asyncio
async def test_redis_failure_after_commit_does_not_remove_db_alert(alert_engine, mock_postgres, mock_redis, caplog):
    mock_redis.publish_alert.side_effect = Exception("Redis Down")

    output = DetectorOutput(
        output_id="out-8",
        input_id="in-8",
        detector_id="ddos_detector",
        threat_type="volumetric_ddos",
        decision=Decision.DETECTION,
        evidence={},
        entity_type="source",
        entity_key="1.2.3.4",
        evaluated_at=1234567890,
        detector_version="1.0",
        source_feature_references=[]
    )
    result = await alert_engine.process_detector_output(output)

    mock_postgres.create_alert.assert_called_once()
    assert "Failed to publish alert" in caplog.text
    # Still returns the payload safely
    assert result is not None
    assert result["alert_id"] == "test-uuid"


@pytest.mark.asyncio
async def test_provenance_preservation(alert_engine, mock_postgres):
    output = DetectorOutput(
        output_id="out-9",
        input_id="in-9",
        detector_id="ddos_detector",
        threat_type="volumetric_ddos",
        decision=Decision.DETECTION,
        evidence={"foo": "bar"},
        entity_type="pair",
        entity_key="1.1.1.1<>2.2.2.2",
        detector_version="1.0",
        model_version="2.0",
        evaluated_at=1234567890,
        source_feature_references=[{"feature_id": "feat-1", "revision": 5}]
    )
    await alert_engine.process_detector_output(output)

    mock_postgres.create_alert.assert_called_once()
    args, kwargs = mock_postgres.create_alert.call_args
    alert = args[0]
    assert alert.detector_id == "ddos_detector"
    assert alert.threat_type == "volumetric_ddos"
    assert alert.entity_type == "pair"
    assert alert.entity_key == "1.1.1.1<>2.2.2.2"
    assert alert.detector_version == "1.0"
    assert alert.model_version == "2.0"
    assert alert.source_feature_references == [{"feature_id": "feat-1", "revision": 5}]


@pytest.mark.asyncio
async def test_redis_payload_is_json_serializable(alert_engine, mock_postgres, mock_redis):
    import json
    import uuid
    # Ensure the fake alert has a real UUID object to test the fix
    real_uuid = uuid.uuid4()
    mock_postgres.create_alert.return_value.alert_id = real_uuid

    output = DetectorOutput(
        output_id="out-json",
        input_id="in-json",
        detector_id="ddos_detector",
        threat_type="volumetric_ddos",
        decision=Decision.DETECTION,
        evidence={"foo": "bar"},
        entity_type="source",
        entity_key="1.2.3.4",
        evaluated_at=1234567890,
        detector_version="1.0",
        source_feature_references=[]
    )

    # Hook mock_redis.publish_alert to actually run json.dumps
    def assert_json_serializable(payload):
        try:
            json.dumps(payload)
        except TypeError as e:
            pytest.fail(f"Payload is not JSON serializable: {e}")

    mock_redis.publish_alert.side_effect = assert_json_serializable

    await alert_engine.process_detector_output(output)
    mock_redis.publish_alert.assert_called_once()
