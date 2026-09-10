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

def create_ddos_record(
    packet_rate: Optional[float] = None,
    byte_rate: Optional[float] = None,
    syn_ratio: Optional[float] = None,
    source_ip_entropy: Optional[float] = None,
    optional_missing: bool = False
) -> DdosFeatureRecord:
    payload = DdosFeaturePayload(
        packet_rate=packet_rate,
        byte_rate=None if optional_missing else (byte_rate if byte_rate is not None else 1000.0),
        syn_ratio=None if optional_missing else (syn_ratio if syn_ratio is not None else 0.5),
        source_ip_entropy=None if optional_missing else (source_ip_entropy if source_ip_entropy is not None else 1.2)
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

@pytest.fixture
def detector() -> DdosDetector:
    return DdosDetector(
        thresholds={"packet_rate": 100.0, "byte_rate": 1000.0, "syn_ratio": 0.5, "source_ip_entropy": 2.0},
        weights={"packet_rate": 0.4, "byte_rate": 0.2, "syn_ratio": 0.2, "source_ip_entropy": 0.2},
        min_triggers=2,
        confidence_cutoff=0.3
    )

@pytest.mark.asyncio
async def test_below_threshold_no_threat(detector):
    # Only one trigger (packet_rate=60, ratio 0.6 >= 0.5), score = 0.6*0.4 = 0.24, triggers=1 < 2
    record = create_ddos_record(packet_rate=60.0, byte_rate=100.0, syn_ratio=0.1, source_ip_entropy=0.1)
    inp = DetectorInput(input_id="inp-1", detector_id=DetectorId.DDOS, feature_record=record)

    outputs = await detector.evaluate([inp])

    assert len(outputs) == 1
    out = outputs[0]
    assert out.decision == Decision.NO_THREAT
    assert out.threat_type == ThreatType.VOLUMETRIC_DDOS
    assert out.evidence["triggered_count"] == 1

@pytest.mark.asyncio
async def test_above_threshold_detection(detector):
    # Triggers: packet_rate (1.0), byte_rate (1.0).
    # Confidence: 0.4*1 + 0.2*1 = 0.6 > 0.3. Triggers=2 >= 2
    record = create_ddos_record(packet_rate=150.0, byte_rate=1500.0, syn_ratio=0.1, source_ip_entropy=0.1)
    inp = DetectorInput(input_id="inp-2", detector_id=DetectorId.DDOS, feature_record=record)

    outputs = await detector.evaluate([inp])

    assert len(outputs) == 1
    out = outputs[0]
    assert out.decision == Decision.DETECTION
    assert out.threat_type == ThreatType.VOLUMETRIC_DDOS
    assert out.confidence >= 0.6
    assert out.evidence["triggered_count"] == 2

@pytest.mark.asyncio
async def test_high_confidence_but_few_triggers(detector):
    # Triggers: packet_rate (1.0). Only 1 trigger, even if weight was huge.
    record = create_ddos_record(packet_rate=200.0, byte_rate=100.0, syn_ratio=0.1, source_ip_entropy=0.1)
    inp = DetectorInput(input_id="inp-3", detector_id=DetectorId.DDOS, feature_record=record)

    outputs = await detector.evaluate([inp])
    out = outputs[0]
    assert out.decision == Decision.NO_THREAT
    assert out.evidence["triggered_count"] == 1

@pytest.mark.asyncio
async def test_none_insufficient_data(detector):
    record = create_ddos_record(packet_rate=None)
    inp = DetectorInput(input_id="inp-4", detector_id=DetectorId.DDOS, feature_record=record)

    outputs = await detector.evaluate([inp])
    out = outputs[0]
    assert out.decision == Decision.INSUFFICIENT_DATA
    assert out.evidence["reason"] == "packet_rate is missing"

@pytest.mark.asyncio
async def test_zero_vs_none(detector):
    record = create_ddos_record(packet_rate=0.0, byte_rate=0.0, syn_ratio=0.0, source_ip_entropy=0.0)
    inp = DetectorInput(input_id="inp-5", detector_id=DetectorId.DDOS, feature_record=record)

    outputs = await detector.evaluate([inp])
    out = outputs[0]
    assert out.decision == Decision.NO_THREAT
    assert out.confidence == 0.0

@pytest.mark.asyncio
async def test_optional_fields_missing(detector):
    # optional_missing=True => byte_rate, syn_ratio, source_ip_entropy are None
    record = create_ddos_record(packet_rate=150.0, optional_missing=True)
    inp = DetectorInput(input_id="inp-6", detector_id=DetectorId.DDOS, feature_record=record)

    outputs = await detector.evaluate([inp])
    out = outputs[0]
    # Packet rate is present, but missing fields count as 0.0, so triggers=1, min_triggers=2 => NO_THREAT
    assert out.decision == Decision.NO_THREAT

@pytest.mark.asyncio
async def test_destination_entity_and_key_preserved(detector):
    record = create_ddos_record(packet_rate=150.0, byte_rate=1500.0)
    inp = DetectorInput(input_id="inp-7", detector_id=DetectorId.DDOS, feature_record=record)

    outputs = await detector.evaluate([inp])
    out = outputs[0]

    assert out.entity_type == EntityType.DESTINATION
    assert out.entity_key == "10.0.0.1"
    assert out.detector_id == DetectorId.DDOS

@pytest.mark.asyncio
async def test_evidence_and_references(detector):
    record = create_ddos_record(packet_rate=150.0, byte_rate=1500.0, syn_ratio=0.1, source_ip_entropy=0.1)
    inp = DetectorInput(input_id="inp-8", detector_id=DetectorId.DDOS, feature_record=record)

    outputs = await detector.evaluate([inp])
    out = outputs[0]

    assert "signals" in out.evidence
    assert len(out.evidence["signals"]) == 4
    packet_rate_evidence = next(s for s in out.evidence["signals"] if s["signal_name"] == "packet_rate")
    assert packet_rate_evidence.get("value") == 150.0
    assert packet_rate_evidence["threshold"] == 100.0
    assert packet_rate_evidence["triggered"] is True

    assert len(out.source_feature_references) == 1
    ref = out.source_feature_references[0]
    assert ref.feature_id == record.feature_id
    assert ref.revision == record.revision

@pytest.mark.asyncio
async def test_invalid_input_rejected(detector):
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
    detector = DdosDetector(
        thresholds={"packet_rate": 500.0},
        weights={"packet_rate": 1.0},
        min_triggers=1,
        confidence_cutoff=0.5
    )
    record = create_ddos_record(packet_rate=300.0, optional_missing=True)
    inp = DetectorInput(input_id="inp-10", detector_id=DetectorId.DDOS, feature_record=record)

    outputs = await detector.evaluate([inp])
    # 300 / 500 = 0.6 -> Triggered=1, Confidence=0.6 -> DETECTION
    assert outputs[0].decision == Decision.DETECTION

    record2 = create_ddos_record(packet_rate=100.0, optional_missing=True)
    inp2 = DetectorInput(input_id="inp-11", detector_id=DetectorId.DDOS, feature_record=record2)
    outputs2 = await detector.evaluate([inp2])
    # 100 / 500 = 0.2 -> Triggered=0 -> NO_THREAT
    assert outputs2[0].decision == Decision.NO_THREAT

@pytest.mark.asyncio
async def test_framework_dispatch():
    registry = DetectorRegistry()
    registry.register(DdosDetector(
        thresholds={"packet_rate": 100.0},
        weights={"packet_rate": 1.0},
        min_triggers=1,
        confidence_cutoff=0.5
    ))
    grouping = DummyPassThroughGrouping()
    router = DetectorRouter(registry, grouping)

    record = create_ddos_record(packet_rate=150.0, optional_missing=True)

    # Send through router
    outputs = await router.route(record)
    assert len(outputs) == 1
    out = outputs[0]

    assert out.detector_id == DetectorId.DDOS
    assert out.decision == Decision.DETECTION
    assert out.threat_type == ThreatType.VOLUMETRIC_DDOS
