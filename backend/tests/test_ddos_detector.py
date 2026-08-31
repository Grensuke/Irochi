import pytest
import uuid
import time
from typing import Optional, List

from app.schemas.features import (
    DdosFeatureRecord,
    DdosFeaturePayload,
    FeatureMechanism,
    DetectorDomain,
    EntityType,
    WindowType,
    ReconFeatureRecord,
    ReconFeaturePayload
)
from app.schemas.detectors import (
    DetectorId,
    Decision,
    DetectorInput,
    ThreatType
)
from app.services.detectors.ddos import DdosDetector
from app.services.detectors.registry import DetectorRegistry
from app.services.detectors.grouping import GroupingInterface
from app.services.detectors.router import DetectorRouter

class DummyPassThroughGrouping(GroupingInterface):
    async def add_and_evaluate(self, detector_input: DetectorInput) -> List[DetectorInput]:
        return [detector_input]
    def get_base_grouping_identity(self, detector_input: DetectorInput) -> str:
        return ""

def create_ddos_record(packet_rate: Optional[float] = None, optional_missing: bool = False) -> DdosFeatureRecord:
    payload = DdosFeaturePayload(
        packet_rate=packet_rate,
        byte_rate=None if optional_missing else 1000.0,
        syn_ratio=None if optional_missing else 0.5,
        source_ip_entropy=None if optional_missing else 1.2
    )
    return DdosFeatureRecord(
        feature_id=str(uuid.uuid4()),
        mechanism=FeatureMechanism.WINDOWED,
        detector_domain=DetectorDomain.DDOS,
        entity_type=EntityType.DESTINATION,
        entity_key="10.0.0.1",
        window_type=WindowType.TUMBLING,
        window_start=int(time.time() * 1000000) - 60000000,
        window_end=int(time.time() * 1000000),
        computed_at=int(time.time() * 1000000),
        schema_version="1.0",
        revision=1,
        provenance={"source_events": ["event1"]},
        payload=payload
    )

@pytest.mark.asyncio
async def test_below_threshold_no_threat():
    detector = DdosDetector(packet_rate_threshold=100.0)
    record = create_ddos_record(packet_rate=50.0)
    inp = DetectorInput(input_id="inp-1", detector_id=DetectorId.DDOS, feature_record=record)

    outputs = await detector.evaluate([inp])

    assert len(outputs) == 1
    out = outputs[0]
    assert out.decision == Decision.NO_THREAT
    assert out.threat_type == ThreatType.VOLUMETRIC_DDOS
    assert out.score == 50.0

@pytest.mark.asyncio
async def test_above_threshold_detection():
    detector = DdosDetector(packet_rate_threshold=100.0)
    record = create_ddos_record(packet_rate=150.0)
    inp = DetectorInput(input_id="inp-2", detector_id=DetectorId.DDOS, feature_record=record)

    outputs = await detector.evaluate([inp])

    assert len(outputs) == 1
    out = outputs[0]
    assert out.decision == Decision.DETECTION
    assert out.threat_type == ThreatType.VOLUMETRIC_DDOS
    assert out.score == 150.0

@pytest.mark.asyncio
async def test_exact_threshold_no_threat():
    detector = DdosDetector(packet_rate_threshold=100.0)
    record = create_ddos_record(packet_rate=100.0)
    inp = DetectorInput(input_id="inp-3", detector_id=DetectorId.DDOS, feature_record=record)

    outputs = await detector.evaluate([inp])
    out = outputs[0]
    assert out.decision == Decision.NO_THREAT

@pytest.mark.asyncio
async def test_none_insufficient_data():
    detector = DdosDetector(packet_rate_threshold=100.0)
    record = create_ddos_record(packet_rate=None)
    inp = DetectorInput(input_id="inp-4", detector_id=DetectorId.DDOS, feature_record=record)

    outputs = await detector.evaluate([inp])
    out = outputs[0]
    assert out.decision == Decision.INSUFFICIENT_DATA
    assert out.evidence["reason"] == "packet_rate is missing"

@pytest.mark.asyncio
async def test_zero_vs_none():
    detector = DdosDetector(packet_rate_threshold=100.0)
    record = create_ddos_record(packet_rate=0.0)
    inp = DetectorInput(input_id="inp-5", detector_id=DetectorId.DDOS, feature_record=record)

    outputs = await detector.evaluate([inp])
    out = outputs[0]
    assert out.decision == Decision.NO_THREAT
    assert out.score == 0.0

@pytest.mark.asyncio
async def test_optional_fields_missing():
    detector = DdosDetector(packet_rate_threshold=100.0)
    record = create_ddos_record(packet_rate=150.0, optional_missing=True)
    inp = DetectorInput(input_id="inp-6", detector_id=DetectorId.DDOS, feature_record=record)

    outputs = await detector.evaluate([inp])
    out = outputs[0]
    assert out.decision == Decision.DETECTION

@pytest.mark.asyncio
async def test_destination_entity_and_key_preserved():
    detector = DdosDetector(packet_rate_threshold=100.0)
    record = create_ddos_record(packet_rate=150.0)
    inp = DetectorInput(input_id="inp-7", detector_id=DetectorId.DDOS, feature_record=record)

    outputs = await detector.evaluate([inp])
    out = outputs[0]

    assert out.entity_type == EntityType.DESTINATION
    assert out.entity_key == "10.0.0.1"
    assert out.detector_id == DetectorId.DDOS

@pytest.mark.asyncio
async def test_evidence_and_references():
    detector = DdosDetector(packet_rate_threshold=100.0)
    record = create_ddos_record(packet_rate=150.0)
    inp = DetectorInput(input_id="inp-8", detector_id=DetectorId.DDOS, feature_record=record)

    outputs = await detector.evaluate([inp])
    out = outputs[0]

    assert out.evidence["feature"] == "packet_rate"
    assert out.evidence["observed"] == 150.0
    assert out.evidence["threshold"] == 100.0
    assert out.evidence["rule"] == "packet_rate > threshold"

    assert len(out.source_feature_references) == 1
    ref = out.source_feature_references[0]
    assert ref.feature_id == record.feature_id
    assert ref.revision == record.revision

@pytest.mark.asyncio
async def test_invalid_input_rejected():
    detector = DdosDetector(packet_rate_threshold=100.0)
    payload = ReconFeaturePayload()
    record = ReconFeatureRecord(
        feature_id="recon-1",
        mechanism=FeatureMechanism.WINDOWED,
        detector_domain=DetectorDomain.RECON,
        entity_type=EntityType.SOURCE,
        entity_key="192.168.1.1",
        window_type=WindowType.TUMBLING,
        window_start=0,
        window_end=10,
        computed_at=0,
        schema_version="1.0",
        revision=1,
        payload=payload
    )
    inp = DetectorInput(input_id="inp-9", detector_id=DetectorId.DDOS, feature_record=record)

    outputs = await detector.evaluate([inp])
    out = outputs[0]
    assert out.decision == Decision.INVALID_INPUT

@pytest.mark.asyncio
async def test_configurable_threshold():
    detector = DdosDetector(packet_rate_threshold=500.0)
    record = create_ddos_record(packet_rate=300.0)
    inp = DetectorInput(input_id="inp-10", detector_id=DetectorId.DDOS, feature_record=record)

    outputs = await detector.evaluate([inp])
    assert outputs[0].decision == Decision.NO_THREAT

    record2 = create_ddos_record(packet_rate=600.0)
    inp2 = DetectorInput(input_id="inp-11", detector_id=DetectorId.DDOS, feature_record=record2)
    outputs2 = await detector.evaluate([inp2])
    assert outputs2[0].decision == Decision.DETECTION

@pytest.mark.asyncio
async def test_framework_dispatch():
    registry = DetectorRegistry()
    registry.register(DdosDetector(packet_rate_threshold=100.0))
    grouping = DummyPassThroughGrouping()
    router = DetectorRouter(registry, grouping)

    record = create_ddos_record(packet_rate=150.0)

    # Send through router
    outputs = await router.route(record)
    assert len(outputs) == 1
    out = outputs[0]

    assert out.detector_id == DetectorId.DDOS
    assert out.decision == Decision.DETECTION
    assert out.threat_type == ThreatType.VOLUMETRIC_DDOS
