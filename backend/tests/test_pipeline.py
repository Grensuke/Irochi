import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.pipeline import DetectionPipeline
from app.services.streaming.consumer import KafkaConsumerService, ConsumerMessage
from app.services.features.engine import FeatureEngine
from app.services.detectors.router import DetectorRouter
from app.services.alert_engine import AlertEngine
from app.services.postgres_alert_service import PostgresAlertService
from app.services.redis_pubsub import RedisPubSubService
from app.schemas.features import DdosFeatureRecord, DdosFeaturePayload, DetectorDomain, EntityType, FeatureMechanism
from app.schemas.detectors import DetectorOutput, DetectorId, Decision, SourceFeatureReference


@pytest.fixture
def mock_consumer():
    return AsyncMock(spec=KafkaConsumerService)


@pytest.fixture
def mock_feature_engine():
    return AsyncMock(spec=FeatureEngine)


@pytest.fixture
def mock_router():
    return AsyncMock(spec=DetectorRouter)


@pytest.fixture
def mock_redis_service():
    return AsyncMock(spec=RedisPubSubService)


@pytest.fixture
def mock_session_factory():
    mock_session = AsyncMock()
    # Mock the async context manager behavior
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    mock_factory = MagicMock(return_value=mock_session)
    return mock_factory


@pytest.fixture
def pipeline(mock_consumer, mock_feature_engine, mock_router, mock_session_factory, mock_redis_service):
    return DetectionPipeline(
        consumer=mock_consumer,
        feature_engine=mock_feature_engine,
        router=mock_router,
        session_factory=mock_session_factory,
        redis_service=mock_redis_service
    )


@pytest.fixture
def sample_message():
    return ConsumerMessage(
        topic="test",
        partition=0,
        offset=1,
        key=None,
        payload={"dummy": "data"}
    )


@pytest.fixture
def sample_feature_record():
    return DdosFeatureRecord(
        feature_id="f1",
        mechanism=FeatureMechanism.WINDOWED,
        detector_domain=DetectorDomain.DDOS,
        entity_type=EntityType.DESTINATION,
        entity_key="10.0.0.1",
        window_type="tumbling",
        window_start=1000,
        window_end=2000,
        computed_at=3000,
        schema_version="1.0",
        revision=1,
        payload=DdosFeaturePayload(packet_rate=50.0)
    )


@pytest.fixture
def sample_detector_output(sample_feature_record):
    return DetectorOutput(
        output_id="o1",
        detector_id=DetectorId.DDOS,
        input_id="i1",
        entity_type=EntityType.DESTINATION,
        entity_key="10.0.0.1",
        evaluated_at=4000,
        detector_version="1.0",
        decision=Decision.DETECTION,
        evidence={},
        source_feature_references=[
            SourceFeatureReference(feature_id=sample_feature_record.feature_id, revision=sample_feature_record.revision)
        ]
    )


@pytest.mark.asyncio
async def test_pipeline_start_stop(pipeline, mock_consumer):
    """Test pipeline start and stop lifecycle."""
    # Ensure consume yields nothing and blocks
    async def infinite_consume():
        while True:
            await asyncio.sleep(1)
            yield None
    mock_consumer.consume = infinite_consume

    assert not pipeline._running
    assert pipeline._task is None

    pipeline.start()
    assert pipeline._running
    assert pipeline._task is not None
    assert not pipeline._task.done()

    await pipeline.stop()
    assert not pipeline._running
    assert pipeline._task is None


@pytest.mark.asyncio
async def test_end_to_end_traversal(
    pipeline, mock_consumer, mock_feature_engine, mock_router, mock_session_factory,
    sample_message, sample_feature_record, sample_detector_output
):
    """One message -> FeatureRecords -> DetectorOutputs -> AlertEngine."""
    async def mock_consume():
        yield sample_message
    mock_consumer.consume = mock_consume

    mock_feature_engine.process.return_value = [sample_feature_record]
    mock_router.route.return_value = [sample_detector_output]

    # We patch AlertEngine to track calls instead of mocking the whole class,
    # since Pipeline constructs AlertEngine internally.
    with patch("app.services.pipeline.AlertEngine.process_detector_output", new_callable=AsyncMock) as mock_alert_engine_process:
        # Run loop directly for testing (it will exit after consuming the single message)
        pipeline._running = True
        await pipeline._run_loop()

        # Validations
        mock_feature_engine.process.assert_called_once_with(sample_message)
        mock_router.route.assert_called_once_with(sample_feature_record)

        # Ensure AlertEngine was called
        mock_alert_engine_process.assert_called_once_with(sample_detector_output)

        # Ensure session was created via the factory
        mock_session_factory.assert_called_once()
        mock_session = mock_session_factory.return_value
        mock_session.__aenter__.assert_called_once()


@pytest.mark.asyncio
async def test_multiple_records_and_outputs(
    pipeline, mock_consumer, mock_feature_engine, mock_router,
    sample_message, sample_feature_record, sample_detector_output
):
    """One message -> multiple FeatureRecords -> multiple DetectorOutputs."""
    async def mock_consume():
        yield sample_message
    mock_consumer.consume = mock_consume

    # Return 2 feature records
    mock_feature_engine.process.return_value = [sample_feature_record, sample_feature_record]

    # Each record returns 2 outputs
    mock_router.route.return_value = [sample_detector_output, sample_detector_output]

    with patch("app.services.pipeline.AlertEngine.process_detector_output", new_callable=AsyncMock) as mock_alert_engine_process:
        pipeline._running = True
        await pipeline._run_loop()

        assert mock_router.route.call_count == 2
        # Total outputs processed = 2 records * 2 outputs = 4
        assert mock_alert_engine_process.call_count == 4


@pytest.mark.asyncio
async def test_empty_feature_engine_result(pipeline, mock_consumer, mock_feature_engine, mock_router):
    """Empty FeatureEngine result does not call DetectorRouter."""
    async def mock_consume():
        yield ConsumerMessage(topic="test", partition=0, offset=1, key=None, payload={})
    mock_consumer.consume = mock_consume

    mock_feature_engine.process.return_value = []

    pipeline._running = True
    await pipeline._run_loop()

    mock_router.route.assert_not_called()


@pytest.mark.asyncio
async def test_empty_detector_router_result(pipeline, mock_consumer, mock_feature_engine, mock_router, sample_message, sample_feature_record):
    """Empty DetectorRouter result does not call AlertEngine."""
    async def mock_consume():
        yield sample_message
    mock_consumer.consume = mock_consume

    mock_feature_engine.process.return_value = [sample_feature_record]
    mock_router.route.return_value = []

    with patch("app.services.pipeline.AlertEngine.process_detector_output", new_callable=AsyncMock) as mock_alert_engine_process:
        pipeline._running = True
        await pipeline._run_loop()

        mock_alert_engine_process.assert_not_called()


@pytest.mark.asyncio
async def test_failed_message_does_not_terminate_pipeline(
    pipeline, mock_consumer, mock_feature_engine, mock_router,
    sample_message, sample_feature_record, sample_detector_output
):
    """An exception during processing one message does not kill the consumer loop."""
    message2 = ConsumerMessage(topic="test", partition=0, offset=2, key=None, payload={"dummy": "2"})

    async def mock_consume():
        yield sample_message
        yield message2
    mock_consumer.consume = mock_consume

    # First message fails in FeatureEngine
    mock_feature_engine.process.side_effect = [Exception("Feature extraction failed"), [sample_feature_record]]
    mock_router.route.return_value = [sample_detector_output]

    with patch("app.services.pipeline.AlertEngine.process_detector_output", new_callable=AsyncMock) as mock_alert_engine_process:
        pipeline._running = True
        await pipeline._run_loop()

        # The loop should have processed the second message despite the first failing
        assert mock_feature_engine.process.call_count == 2
        mock_router.route.assert_called_once_with(sample_feature_record)
        mock_alert_engine_process.assert_called_once_with(sample_detector_output)


@pytest.mark.asyncio
async def test_alert_engine_exception_caught(
    pipeline, mock_consumer, mock_feature_engine, mock_router,
    sample_message, sample_feature_record, sample_detector_output
):
    """Exception injected into AlertEngine is caught and loop continues."""
    async def mock_consume():
        yield sample_message
    mock_consumer.consume = mock_consume

    mock_feature_engine.process.return_value = [sample_feature_record]
    mock_router.route.return_value = [sample_detector_output]

    with patch("app.services.pipeline.AlertEngine.process_detector_output", new_callable=AsyncMock) as mock_alert_engine_process:
        mock_alert_engine_process.side_effect = Exception("DB failure")

        pipeline._running = True
        # Should not raise exception
        await pipeline._run_loop()

        mock_alert_engine_process.assert_called_once_with(sample_detector_output)

@pytest.mark.asyncio
async def test_alert_engine_returns_none(
    pipeline, mock_consumer, mock_feature_engine, mock_router,
    sample_message, sample_feature_record, sample_detector_output
):
    """AlertEngine returning None does not cause issues."""
    async def mock_consume():
        yield sample_message
    mock_consumer.consume = mock_consume

    mock_feature_engine.process.return_value = [sample_feature_record]
    mock_router.route.return_value = [sample_detector_output]

    with patch("app.services.pipeline.AlertEngine.process_detector_output", new_callable=AsyncMock) as mock_alert_engine_process:
        mock_alert_engine_process.return_value = None

        pipeline._running = True
        await pipeline._run_loop()

        mock_alert_engine_process.assert_called_once_with(sample_detector_output)
