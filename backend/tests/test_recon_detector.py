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

def create_recon_record(
    unique_ports: Optional[int] = None,
    unique_hosts: Optional[int] = None,
    scan_rate: Optional[float] = None,
    connection_fan_out: Optional[float] = None,
    optional_missing: bool = False
) -> ReconFeatureRecord:
    payload = ReconFeaturePayload(
        unique_destination_ports=unique_ports,
        unique_destination_hosts=None if optional_missing else (unique_hosts if unique_hosts is not None else 5),
        scan_rate=None if optional_missing else (scan_rate if scan_rate is not None else 2.5),
        connection_fan_out=None if optional_missing else (connection_fan_out if connection_fan_out is not None else 1.0)
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

@pytest.fixture
def detector() -> ReconDetector:
    return ReconDetector(
        thresholds={"unique_destination_ports": 50.0, "unique_destination_hosts": 20.0, "scan_rate": 10.0, "connection_fan_out": 0.8},
        weights={"unique_destination_ports": 0.4, "unique_destination_hosts": 0.3, "scan_rate": 0.2, "connection_fan_out": 0.1},
        min_triggers=1,
        confidence_cutoff=0.3
    )

@pytest.mark.asyncio
async def test_below_threshold_no_threat(detector):
    # Triggers: 0 (since max value is < 0.5 * threshold for all)
    record = create_recon_record(unique_ports=20, unique_hosts=5, scan_rate=2.0, connection_fan_out=0.2)
    inp = DetectorInput(input_id="inp-1", detector_id=DetectorId.RECON, feature_record=record)

    outputs = await detector.evaluate([inp])

    assert len(outputs) == 1
    out = outputs[0]
    assert out.decision == Decision.NO_THREAT
    assert out.threat_type == ThreatType.RECON_PORTSCAN
    assert out.evidence["triggered_count"] == 0

@pytest.mark.asyncio
async def test_above_threshold_detection(detector):
    # Triggers: unique_ports (60/50 > 1), unique_hosts (1/20 < 0.5) => vertical scan
    record = create_recon_record(unique_ports=60, unique_hosts=1, scan_rate=15.0, connection_fan_out=0.1)
    inp = DetectorInput(input_id="inp-2", detector_id=DetectorId.RECON, feature_record=record)

    outputs = await detector.evaluate([inp])

    assert len(outputs) == 1
    out = outputs[0]
    assert out.decision == Decision.DETECTION
    assert out.threat_type == ThreatType.RECON_PORTSCAN
    # ports score = 1.0 * 0.4 = 0.4
    # hosts score = 1/20 * 0.3 = 0.015
    # scan_rate score = 1.0 * 0.2 = 0.2
    # total conf = 0.615 > 0.3
    assert out.confidence >= 0.6
    assert out.evidence["triggered_count"] >= 2

@pytest.mark.asyncio
async def test_none_insufficient_data(detector):
    record = create_recon_record(unique_ports=None)
    inp = DetectorInput(input_id="inp-4", detector_id=DetectorId.RECON, feature_record=record)

    outputs = await detector.evaluate([inp])
    out = outputs[0]
    assert out.decision == Decision.INSUFFICIENT_DATA
    assert out.evidence["reason"] == "unique_destination_ports is missing"

@pytest.mark.asyncio
async def test_optional_fields_missing(detector):
    # Only ports provided. 60/50 = 1.0 trigger, conf = 0.4 > 0.3
    record = create_recon_record(unique_ports=60, optional_missing=True)
    inp = DetectorInput(input_id="inp-5", detector_id=DetectorId.RECON, feature_record=record)

    outputs = await detector.evaluate([inp])
    out = outputs[0]
    assert out.decision == Decision.DETECTION

@pytest.mark.asyncio
async def test_horizontal_scan(detector):
    # Few ports, many hosts.
    record = create_recon_record(unique_ports=1, unique_hosts=50, scan_rate=5.0, connection_fan_out=0.9)
    inp = DetectorInput(input_id="inp-h", detector_id=DetectorId.RECON, feature_record=record)

    outputs = await detector.evaluate([inp])
    out = outputs[0]
    # hosts conf: 1.0 * 0.3 = 0.3, fan_out conf: 1.0 * 0.1 = 0.1, total = 0.4 > 0.3
    assert out.decision == Decision.DETECTION
    assert out.evidence["triggered_count"] >= 2

@pytest.mark.asyncio
async def test_source_entity_and_key_preserved(detector):
    record = create_recon_record(unique_ports=60)
    inp = DetectorInput(input_id="inp-6", detector_id=DetectorId.RECON, feature_record=record)

    outputs = await detector.evaluate([inp])
    out = outputs[0]

    assert out.entity_type == EntityType.SOURCE
    assert out.entity_key == "192.168.1.10"
    assert out.detector_id == DetectorId.RECON

@pytest.mark.asyncio
async def test_evidence_and_references(detector):
    record = create_recon_record(unique_ports=60)
    inp = DetectorInput(input_id="inp-7", detector_id=DetectorId.RECON, feature_record=record)

    outputs = await detector.evaluate([inp])
    out = outputs[0]

    assert "signals" in out.evidence
    assert len(out.evidence["signals"]) == 4
    port_evidence = next(s for s in out.evidence["signals"] if s["signal_name"] == "unique_destination_ports")
    assert port_evidence["value"] == 60
    assert port_evidence["threshold"] == 50.0
    assert port_evidence["triggered"] is True

    assert len(out.source_feature_references) == 1
    ref = out.source_feature_references[0]
    assert ref.feature_id == record.feature_id
    assert ref.revision == record.revision

@pytest.mark.asyncio
async def test_invalid_input_rejected(detector):
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
    detector = ReconDetector(
        thresholds={"unique_destination_ports": 100.0},
        weights={"unique_destination_ports": 1.0},
        min_triggers=1,
        confidence_cutoff=0.5
    )
    record = create_recon_record(unique_ports=80, optional_missing=True)
    inp = DetectorInput(input_id="inp-9", detector_id=DetectorId.RECON, feature_record=record)

    outputs = await detector.evaluate([inp])
    # 80/100 = 0.8 conf, > 0.5
    assert outputs[0].decision == Decision.DETECTION

    record2 = create_recon_record(unique_ports=30, optional_missing=True)
    inp2 = DetectorInput(input_id="inp-10", detector_id=DetectorId.RECON, feature_record=record2)
    outputs2 = await detector.evaluate([inp2])
    # 30/100 = 0.3 conf
    assert outputs2[0].decision == Decision.NO_THREAT

@pytest.mark.asyncio
async def test_framework_dispatch():
    registry = DetectorRegistry()
    registry.register(ReconDetector(
        thresholds={"unique_destination_ports": 20.0},
        weights={"unique_destination_ports": 1.0},
        min_triggers=1,
        confidence_cutoff=0.5
    ))
    grouping = DummyPassThroughGrouping()
    router = DetectorRouter(registry, grouping)

    record = create_recon_record(unique_ports=30, optional_missing=True)

    # Send through router
    outputs = await router.route(record)
    assert len(outputs) == 1
    out = outputs[0]

    assert out.detector_id == DetectorId.RECON
    assert out.decision == Decision.DETECTION
    assert out.threat_type == ThreatType.RECON_PORTSCAN
