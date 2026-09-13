import pytest
from app.schemas.detectors import DetectorInput, Decision, ThreatType
from app.schemas.features import (
    ExfilFeatureRecord,
    ExfilFeaturePayload,
    EntityType,
    DetectorDomain,
    FeatureMechanism
)
from app.schemas.detectors import DetectorId
from app.services.detectors.exfil import ExfiltrationDetector

@pytest.fixture
def detector():
    return ExfiltrationDetector()

def create_input(ratio=None, rate=None):
    payload = ExfilFeaturePayload(
        outbound_inbound_ratio=ratio,
        byte_rate=rate
    )
    
    record = ExfilFeatureRecord(
        feature_id="feat-1",
        mechanism=FeatureMechanism.WINDOWED,
        detector_domain=DetectorDomain.EXFIL,
        entity_type=EntityType.SOURCE,
        entity_key="10.0.0.1",
        computed_at=1000,
        schema_version="1.0",
        revision=1,
        provenance={"source_events": ["event1"]},
        payload=payload
    )
    return DetectorInput(input_id="in-1", detector_id=DetectorId.EXFILTRATION, feature_record=record)

@pytest.mark.asyncio
async def test_exfil_detector_insufficient_data(detector):
    inputs = [create_input(ratio=None, rate=None)]
    outputs = await detector.evaluate(inputs)
    assert len(outputs) == 1
    assert outputs[0].decision == Decision.INSUFFICIENT_DATA

@pytest.mark.asyncio
async def test_exfil_detector_no_threat(detector):
    inputs = [create_input(ratio=1.0, rate=1000)]
    outputs = await detector.evaluate(inputs)
    assert len(outputs) == 1
    assert outputs[0].decision == Decision.NO_THREAT
    assert outputs[0].confidence < 0.60

@pytest.mark.asyncio
async def test_exfil_detector_detection(detector):
    inputs = [create_input(ratio=10.0, rate=100_000)]
    outputs = await detector.evaluate(inputs)
    assert len(outputs) == 1
    assert outputs[0].decision == Decision.DETECTION
    assert outputs[0].threat_type == ThreatType.DATA_EXFILTRATION
    assert outputs[0].confidence > 0.60
    assert outputs[0].evidence["triggered_count"] >= 2
