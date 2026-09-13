import pytest
from app.schemas.detectors import DetectorInput, Decision, ThreatType
from app.schemas.features import (
    TlsC2FeatureRecord,
    TlsC2FeaturePayload,
    EntityType,
    DetectorDomain,
    FeatureMechanism
)
from app.schemas.detectors import DetectorId
from app.services.detectors.c2 import C2Detector

@pytest.fixture
def detector():
    return C2Detector()

def create_input(freq=None, regularity=None, jitter=None, ja3=None):
    payload = TlsC2FeaturePayload(
        connection_frequency=freq,
        timing_regularity=regularity,
        jitter=jitter,
        ja3_blacklist_match=ja3
    )
    record = TlsC2FeatureRecord(
        feature_id="feat-1",
        mechanism=FeatureMechanism.WINDOWED,
        detector_domain=DetectorDomain.TLS_C2,
        entity_type=EntityType.PAIR,
        entity_key="10.0.0.1:10.0.0.2",
        computed_at=1000,
        schema_version="1.0",
        revision=1,
        provenance={"source_events": ["event1"]},
        payload=payload
    )
    return DetectorInput(input_id="in-1", detector_id=DetectorId.TLS_C2, feature_record=record)

@pytest.mark.asyncio
async def test_c2_detector_insufficient_data(detector):
    inputs = [create_input(freq=None, regularity=None, jitter=None)]
    outputs = await detector.evaluate(inputs)
    assert len(outputs) == 1
    assert outputs[0].decision == Decision.INSUFFICIENT_DATA

@pytest.mark.asyncio
async def test_c2_detector_no_threat(detector):
    # High frequency, but very low regularity and high jitter = non-beaconing noise
    inputs = [create_input(freq=20.0, regularity=0.1, jitter=2.0)]
    outputs = await detector.evaluate(inputs)
    assert len(outputs) == 1
    assert outputs[0].decision == Decision.NO_THREAT
    assert outputs[0].confidence < 0.60

@pytest.mark.asyncio
async def test_c2_detector_detection(detector):
    # High frequency, high regularity, very low jitter
    inputs = [create_input(freq=15.0, regularity=0.9, jitter=0.1)]
    outputs = await detector.evaluate(inputs)
    assert len(outputs) == 1
    assert outputs[0].decision == Decision.DETECTION
    assert outputs[0].threat_type == ThreatType.C2_BEACONING
    assert outputs[0].confidence >= 0.60
    assert outputs[0].evidence["triggered_count"] >= 2
