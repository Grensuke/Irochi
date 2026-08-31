import pytest
import uuid
import time
from typing import Optional, List

from app.schemas.features import (
    ReconFeatureRecord,
    ReconFeaturePayload,
    FeatureMechanism,
    DetectorDomain,
    EntityType,
    WindowType,
    DdosFeatureRecord,
    DdosFeaturePayload
)
from app.schemas.detectors import (
    DetectorId,
    Decision,
    DetectorInput,
    ThreatType
)
from app.services.detectors.recon import ReconDetector
from app.services.detectors.registry import DetectorRegistry
from app.services.detectors.grouping import GroupingInterface
from app.services.detectors.router import DetectorRouter

class DummyPassThroughGrouping(GroupingInterface):
    async def add_and_evaluate(self, detector_input: DetectorInput) -> List[DetectorInput]:
        return [detector_input]
    def get_base_grouping_identity(self, detector_input: DetectorInput) -> str:
        return ""

def create_recon_record(unique_ports: Optional[int] = None, optional_missing: bool = False) -> ReconFeatureRecord:
    payload = ReconFeaturePayload(
        unique_destination_ports=unique_ports,
        unique_destination_hosts=None if optional_missing else 5,
        connection_fan_out=None if optional_missing else 10,
        scan_rate=None if optional_missing else 2.5
    )
    return ReconFeatureRecord(
        feature_id=str(uuid.uuid4()),
        mechanism=FeatureMechanism.WINDOWED,
        detector_domain=DetectorDomain.RECON,
        entity_type=EntityType.SOURCE,
        entity_key="192.168.1.10",
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
    detector = ReconDetector(portscan_threshold=50)
    record = create_recon_record(unique_ports=40)
    inp = DetectorInput(input_id="inp-1", detector_id=DetectorId.RECON, feature_record=record)

    outputs = await detector.evaluate([inp])

    assert len(outputs) == 1
    out = outputs[0]
    assert out.decision == Decision.NO_THREAT
    assert out.threat_type == ThreatType.RECON_PORTSCAN
    assert out.score == 40.0

@pytest.mark.asyncio
async def test_above_threshold_detection():
    detector = ReconDetector(portscan_threshold=50)
    record = create_recon_record(unique_ports=60)
    inp = DetectorInput(input_id="inp-2", detector_id=DetectorId.RECON, feature_record=record)

    outputs = await detector.evaluate([inp])

    assert len(outputs) == 1
    out = outputs[0]
    assert out.decision == Decision.DETECTION
    assert out.threat_type == ThreatType.RECON_PORTSCAN
    assert out.score == 60.0

@pytest.mark.asyncio
async def test_exact_threshold_no_threat():
    detector = ReconDetector(portscan_threshold=50)
    record = create_recon_record(unique_ports=50)
    inp = DetectorInput(input_id="inp-3", detector_id=DetectorId.RECON, feature_record=record)

    outputs = await detector.evaluate([inp])

    assert len(outputs) == 1
    out = outputs[0]
    assert out.decision == Decision.NO_THREAT

@pytest.mark.asyncio
async def test_none_insufficient_data():
    detector = ReconDetector(portscan_threshold=50)
    record = create_recon_record(unique_ports=None)
    inp = DetectorInput(input_id="inp-4", detector_id=DetectorId.RECON, feature_record=record)

    outputs = await detector.evaluate([inp])

    assert len(outputs) == 1
    out = outputs[0]
    assert out.decision == Decision.INSUFFICIENT_DATA
    assert out.evidence["reason"] == "unique_destination_ports is missing"

@pytest.mark.asyncio
async def test_optional_fields_missing():
    detector = ReconDetector(portscan_threshold=50)
    record = create_recon_record(unique_ports=60, optional_missing=True)
    inp = DetectorInput(input_id="inp-5", detector_id=DetectorId.RECON, feature_record=record)

    outputs = await detector.evaluate([inp])

    assert len(outputs) == 1
    out = outputs[0]
    assert out.decision == Decision.DETECTION

@pytest.mark.asyncio
async def test_source_entity_and_key_preserved():
    detector = ReconDetector(portscan_threshold=50)
    record = create_recon_record(unique_ports=60)
    inp = DetectorInput(input_id="inp-6", detector_id=DetectorId.RECON, feature_record=record)

    outputs = await detector.evaluate([inp])
    out = outputs[0]

    assert out.entity_type == EntityType.SOURCE
    assert out.entity_key == "192.168.1.10"
    assert out.detector_id == DetectorId.RECON

@pytest.mark.asyncio
async def test_evidence_and_references():
    detector = ReconDetector(portscan_threshold=50)
    record = create_recon_record(unique_ports=60)
    inp = DetectorInput(input_id="inp-7", detector_id=DetectorId.RECON, feature_record=record)

    outputs = await detector.evaluate([inp])
    out = outputs[0]

    assert out.evidence["feature"] == "unique_destination_ports"
    assert out.evidence["observed"] == 60
    assert out.evidence["threshold"] == 50
    assert out.evidence["rule"] == "unique_destination_ports > threshold"

    assert len(out.source_feature_references) == 1
    ref = out.source_feature_references[0]
    assert ref.feature_id == record.feature_id
    assert ref.revision == record.revision

@pytest.mark.asyncio
async def test_invalid_input_rejected():
    detector = ReconDetector(portscan_threshold=50)
    # Give a DdosFeatureRecord instead
    payload = DdosFeaturePayload()
    record = DdosFeatureRecord(
        feature_id="ddos-1",
        mechanism=FeatureMechanism.WINDOWED,
        detector_domain=DetectorDomain.DDOS,
        entity_type=EntityType.DESTINATION,
        entity_key="10.0.0.1",
        window_type=WindowType.TUMBLING,
        window_start=0,
        window_end=10,
        computed_at=0,
        schema_version="1.0",
        revision=1,
        payload=payload
    )
    inp = DetectorInput(input_id="inp-8", detector_id=DetectorId.RECON, feature_record=record)

    outputs = await detector.evaluate([inp])
    out = outputs[0]
    assert out.decision == Decision.INVALID_INPUT

@pytest.mark.asyncio
async def test_configurable_threshold():
    detector = ReconDetector(portscan_threshold=100)
    record = create_recon_record(unique_ports=80)
    inp = DetectorInput(input_id="inp-9", detector_id=DetectorId.RECON, feature_record=record)

    outputs = await detector.evaluate([inp])
    assert outputs[0].decision == Decision.NO_THREAT

    record2 = create_recon_record(unique_ports=110)
    inp2 = DetectorInput(input_id="inp-10", detector_id=DetectorId.RECON, feature_record=record2)
    outputs2 = await detector.evaluate([inp2])
    assert outputs2[0].decision == Decision.DETECTION

@pytest.mark.asyncio
async def test_framework_dispatch():
    registry = DetectorRegistry()
    registry.register(ReconDetector(portscan_threshold=20))
    grouping = DummyPassThroughGrouping()
    router = DetectorRouter(registry, grouping)

    record = create_recon_record(unique_ports=30)

    # Send through router
    outputs = await router.route(record)
    assert len(outputs) == 1
    out = outputs[0]

    assert out.detector_id == DetectorId.RECON
    assert out.decision == Decision.DETECTION
    assert out.threat_type == ThreatType.RECON_PORTSCAN
