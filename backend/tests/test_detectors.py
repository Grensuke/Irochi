import pytest
from typing import List
import uuid

from app.schemas.features import (
    FeatureMechanism, DetectorDomain, EntityType, WindowType,
    CorrelationStatus, DdosFeaturePayload, DnsFeaturePayload, TlsC2FeaturePayload,
    DdosFeatureRecord, DnsFeatureRecord, TlsC2FeatureRecord, ReconFeatureRecord, ReconFeaturePayload
)
from app.schemas.detectors import (
    DetectorId, Decision, DetectorInput, DetectorOutput, Severity, ThreatType, SourceFeatureReference
)
from app.services.detectors.base import BaseDetector
from app.services.detectors.registry import DetectorRegistry
from app.services.detectors.grouping import GroupingInterface
from app.services.detectors.router import DetectorRouter

# --- Test Doubles ---

class DummyDetector(BaseDetector):
    def __init__(self, detector_id: DetectorId):
        self._detector_id = detector_id

    @property
    def detector_id(self) -> DetectorId:
        return self._detector_id

    @property
    def detector_version(self) -> str:
        return "1.0.0"

    async def evaluate(self, inputs: List[DetectorInput]) -> List[DetectorOutput]:
        if not inputs:
            return []

        first_input = inputs[0]
        # Just echo back a success for testing framework boundary
        out = DetectorOutput(
            output_id=str(uuid.uuid4()),
            detector_id=self.detector_id,
            input_id=first_input.input_id,
            entity_type=first_input.feature_record.entity_type,
            entity_key=first_input.feature_record.entity_key,
            evaluated_at=1000000,
            detector_version=self.detector_version,
            decision=Decision.NO_THREAT,
            confidence=0.99,
            source_feature_references=[
                SourceFeatureReference(
                    feature_id=i.feature_record.feature_id,
                    revision=i.feature_record.revision
                ) for i in inputs
            ]
        )
        return [out]

class DummyPassThroughGrouping(GroupingInterface):
    """A grouping interface that just passes records through immediately."""
    async def add_and_evaluate(self, detector_input: DetectorInput) -> List[DetectorInput]:
        return [detector_input]

class DummyAccumulateGrouping(GroupingInterface):
    """A grouping interface that requires 2 records before evaluating."""
    def __init__(self):
        self.buffer = []

    async def add_and_evaluate(self, detector_input: DetectorInput) -> List[DetectorInput]:
        self.buffer.append(detector_input)
        if len(self.buffer) >= 2:
            res = self.buffer.copy()
            self.buffer.clear()
            return res
        return []

# --- Fixtures ---

@pytest.fixture
def registry():
    return DetectorRegistry()

@pytest.fixture
def router(registry):
    return DetectorRouter(registry, DummyPassThroughGrouping())

def create_valid_ddos_record() -> DdosFeatureRecord:
    return DdosFeatureRecord(
        feature_id="feat-1",
        mechanism=FeatureMechanism.WINDOWED,
        detector_domain=DetectorDomain.DDOS,
        entity_type=EntityType.DESTINATION,
        entity_key="1.1.1.1",
        window_type=WindowType.SLIDING,
        window_start=1000,
        window_end=2000,
        computed_at=2500,
        schema_version="1.0",
        revision=1,
        payload=DdosFeaturePayload(
            packet_rate=100.0,
            byte_rate=None, # Missing != Zero test
            syn_ratio=0.5,
            source_ip_entropy=2.1
        )
    )

def create_valid_tls_enrichment() -> TlsC2FeatureRecord:
    return TlsC2FeatureRecord(
        feature_id="feat-2",
        mechanism=FeatureMechanism.ENRICHMENT,
        detector_domain=DetectorDomain.TLS_C2,
        entity_type=EntityType.CONNECTION,
        entity_key="conn-1",
        computed_at=2500,
        schema_version="1.0",
        revision=2,
        payload=TlsC2FeaturePayload(
            ja3_blacklist_match=True
        )
    )

# --- Tests ---

@pytest.mark.asyncio
async def test_registry_registration(registry):
    det = DummyDetector(DetectorId.DDOS)
    registry.register(det)
    assert registry.is_registered(DetectorId.DDOS)
    assert registry.get_detector(DetectorId.DDOS) == det

    with pytest.raises(ValueError):
        registry.register(det)

@pytest.mark.asyncio
async def test_valid_detector_mapping_and_dispatch(registry, router):
    registry.register(DummyDetector(DetectorId.DDOS))
    record = create_valid_ddos_record()

    outputs = await router.route(record)
    assert len(outputs) == 1

    output = outputs[0]
    assert output.decision == Decision.NO_THREAT
    assert output.detector_id == DetectorId.DDOS
    assert len(output.source_feature_references) == 1
    assert output.source_feature_references[0].feature_id == "feat-1"
    assert output.source_feature_references[0].revision == 1

@pytest.mark.asyncio
async def test_invalid_detector_handling(router):
    # Route without registering detector
    record = create_valid_ddos_record()
    outputs = await router.route(record)
    assert len(outputs) == 1
    assert outputs[0].decision == Decision.DETECTOR_ERROR

@pytest.mark.asyncio
async def test_mechanism_entity_compatibility(router):
    # Invalid: DDoS with SOURCE
    record = create_valid_ddos_record()
    record.entity_type = EntityType.SOURCE
    outputs = await router.route(record)
    assert outputs[0].decision == Decision.INVALID_INPUT

    # Valid: TLS/C2 with PAIR (Windowed)
    tls_record = create_valid_tls_enrichment()
    tls_record.mechanism = FeatureMechanism.WINDOWED
    tls_record.entity_type = EntityType.PAIR
    tls_record.window_type = WindowType.SLIDING
    tls_record.window_start = 1000
    tls_record.window_end = 2000
    outputs = await router.route(tls_record)
    assert outputs[0].decision == Decision.DETECTOR_ERROR # Error is fine, it passed validation but no detector registered

@pytest.mark.asyncio
async def test_tls_mixed_entity_contexts(registry, router):
    registry.register(DummyDetector(DetectorId.TLS_C2))

    # Connection / Enrichment
    rec1 = create_valid_tls_enrichment()
    out1 = await router.route(rec1)
    assert out1[0].decision == Decision.NO_THREAT

    # Pair / Windowed
    rec2 = create_valid_tls_enrichment()
    rec2.mechanism = FeatureMechanism.WINDOWED
    rec2.entity_type = EntityType.PAIR
    rec2.window_type = WindowType.SLIDING
    rec2.window_start = 1000
    rec2.window_end = 2000
    out2 = await router.route(rec2)
    assert out2[0].decision == Decision.NO_THREAT

@pytest.mark.asyncio
async def test_window_metadata_validation(router):
    # Windowed record without window fields
    record = create_valid_ddos_record()
    record.window_start = None
    outputs = await router.route(record)
    assert outputs[0].decision == Decision.INVALID_INPUT

    # Enrichment record with window fields
    rec2 = create_valid_tls_enrichment()
    rec2.window_type = WindowType.TUMBLING
    outputs2 = await router.route(rec2)
    assert outputs2[0].decision == Decision.INVALID_INPUT

@pytest.mark.asyncio
async def test_missing_not_zero():
    # Verify missing fields are None, not 0
    record = create_valid_ddos_record()
    assert record.payload.byte_rate is None
    assert record.payload.packet_rate == 100.0

@pytest.mark.asyncio
async def test_grouping_identity():
    grouping = DummyPassThroughGrouping()
    rec = create_valid_ddos_record()
    inp = DetectorInput(input_id="1", detector_id=DetectorId.DDOS, feature_record=rec)
    ident = grouping.get_base_grouping_identity(inp)
    assert ident == (DetectorId.DDOS, EntityType.DESTINATION, "1.1.1.1")

@pytest.mark.asyncio
async def test_multi_record_grouping(registry):
    grouping = DummyAccumulateGrouping()
    router = DetectorRouter(registry, grouping)
    registry.register(DummyDetector(DetectorId.TLS_C2))

    rec1 = create_valid_tls_enrichment()
    rec1.feature_id = "feat-a"
    out1 = await router.route(rec1)
    assert len(out1) == 0 # Buffered

    rec2 = create_valid_tls_enrichment()
    rec2.feature_id = "feat-b"
    out2 = await router.route(rec2)
    assert len(out2) == 1 # Evaluated

    assert len(out2[0].source_feature_references) == 2
    assert out2[0].source_feature_references[0].feature_id == "feat-a"
    assert out2[0].source_feature_references[1].feature_id == "feat-b"

@pytest.mark.asyncio
async def test_detector_output_schema_validation():
    # Test valid output
    out = DetectorOutput(
        output_id="out-1",
        detector_id=DetectorId.DDOS,
        input_id="in-1",
        entity_type=EntityType.DESTINATION,
        entity_key="1.1.1.1",
        evaluated_at=1000,
        detector_version="1.0",
        decision=Decision.DETECTION,
        threat_type=ThreatType.VOLUMETRIC_DDOS,
        confidence=0.8,
        severity_candidate=Severity.HIGH,
        source_feature_references=[
            SourceFeatureReference(feature_id="f1", revision=1)
        ]
    )
    assert out.decision == Decision.DETECTION
    assert out.threat_type == ThreatType.VOLUMETRIC_DDOS

@pytest.mark.asyncio
async def test_unknown_domain_handling(router):
    record = create_valid_ddos_record()
    # Bypass pydantic validation for the test to simulate an unmapped domain
    object.__setattr__(record, 'detector_domain', "unknown_future_domain")

    with pytest.raises(ValueError, match="Unsupported detector domain"):
        await router.route(record)
