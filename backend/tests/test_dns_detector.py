import pytest
from app.schemas.canonical import CanonicalEvent, EventType
from app.schemas.features import DnsFeatureRecord, DnsFeaturePayload, FeatureRecordEnvelope
from app.schemas.detectors import DetectorInput, DetectorId, ThreatType, Decision, EntityType
from app.services.detectors.dns import DnsDetector
from app.services.detectors.router import DetectorRouter
from app.services.detectors.registry import DetectorRegistry
from app.services.detectors.grouping import GroupingInterface

class MockGrouping(GroupingInterface):
    async def add_and_evaluate(self, detector_input: DetectorInput) -> list:
        return [detector_input]
    def get_base_grouping_identity(self, detector_input: DetectorInput) -> str:
        return "mock"

class MockModel:
    def __init__(self, prob):
        self.prob = prob
    def predict_proba(self, X):
        return [[1 - self.prob, self.prob]]

@pytest.fixture
def dns_detector(monkeypatch):
    detector = DnsDetector()
    # Mock load
    detector.model = MockModel(0.95)
    detector.metadata = {
        "model_version": "v1.mock",
        "threshold": 0.80,
        "feature_order": [
            "query_length",
            "label_count",
            "max_label_length",
            "domain_entropy",
            "vowel_consonant_ratio",
            "digit_ratio"
        ]
    }
    detector.threshold = 0.80
    return detector

def create_mock_dns_record(payload_kwargs) -> DnsFeatureRecord:
    from app.schemas.features import FeatureMechanism
    import uuid
    import time
    return DnsFeatureRecord(
        feature_id=str(uuid.uuid4()),
        event_id="evt-1",
        mechanism=FeatureMechanism.ENRICHMENT,
        timestamp=1000,
        computed_at=int(time.time()),
        schema_version="1.0",
        revision=1,
        entity_type=EntityType.SOURCE,
        entity_key="10.0.0.1",
        source_event_type=EventType.DNS,
        payload=DnsFeaturePayload(**payload_kwargs)
    )

@pytest.mark.asyncio
async def test_benign_domain(dns_detector):
    dns_detector.model = MockModel(0.10) # 10% DGA prob
    record = create_mock_dns_record({
        "query_length": 10,
        "label_count": 2,
        "max_label_length": 6,
        "domain_entropy": 2.5,
        "vowel_consonant_ratio": 0.5,
        "digit_ratio": 0.0
    })

    input_data = DetectorInput(
        input_id="in-1",
        detector_id=DetectorId.DNS_DGA_TUNNEL,
        feature_record=record
    )

    outputs = await dns_detector.evaluate([input_data])
    output = outputs[0]

    assert output.decision == Decision.NO_THREAT
    assert output.score == 0.10
    assert output.confidence is None
    assert output.evidence["threshold"] == 0.80

@pytest.mark.asyncio
async def test_dga_domain(dns_detector):
    dns_detector.model = MockModel(0.95) # 95% DGA prob
    record = create_mock_dns_record({
        "query_length": 15,
        "label_count": 2,
        "max_label_length": 11,
        "domain_entropy": 3.8,
        "vowel_consonant_ratio": 0.1,
        "digit_ratio": 0.3
    })

    input_data = DetectorInput(
        input_id="in-2",
        detector_id=DetectorId.DNS_DGA_TUNNEL,
        feature_record=record
    )

    outputs = await dns_detector.evaluate([input_data])
    output = outputs[0]

    assert output.decision == Decision.DETECTION
    assert output.score == 0.95
    assert output.threat_type == ThreatType.DGA_DNS_TUNNEL
    assert output.evidence["model_version"] == "v1.mock"

@pytest.mark.asyncio
async def test_missing_query(dns_detector):
    record = create_mock_dns_record({
        "query_length": None,
    })
    input_data = DetectorInput(input_id="in-3", detector_id=DetectorId.DNS_DGA_TUNNEL, feature_record=record)

    outputs = await dns_detector.evaluate([input_data])
    output = outputs[0]

    assert output.decision == Decision.INSUFFICIENT_DATA

@pytest.mark.asyncio
async def test_malformed_domain(dns_detector):
    record = create_mock_dns_record({
        "query_length": 15,
        # missing label_count
        "max_label_length": 11,
        "domain_entropy": 3.8,
        "vowel_consonant_ratio": 0.1,
        "digit_ratio": 0.3
    })
    input_data = DetectorInput(input_id="in-4", detector_id=DetectorId.DNS_DGA_TUNNEL, feature_record=record)

    outputs = await dns_detector.evaluate([input_data])
    output = outputs[0]

    assert output.decision == Decision.INVALID_INPUT

@pytest.mark.asyncio
async def test_model_load_failure():
    detector = DnsDetector()
    detector.model = None # Force unload

    record = create_mock_dns_record({
        "query_length": 10,
        "label_count": 2,
        "max_label_length": 6,
        "domain_entropy": 2.5,
        "vowel_consonant_ratio": 0.5,
        "digit_ratio": 0.0
    })
    input_data = DetectorInput(input_id="in-5", detector_id=DetectorId.DNS_DGA_TUNNEL, feature_record=record)

    outputs = await detector.evaluate([input_data])
    output = outputs[0]
    assert output.decision == Decision.DETECTOR_ERROR

@pytest.mark.asyncio
async def test_detector_router_dispatch(dns_detector):
    registry = DetectorRegistry()
    registry.register(dns_detector)

    router = DetectorRouter(registry, MockGrouping())

    record = create_mock_dns_record({
        "query_length": 15,
        "label_count": 2,
        "max_label_length": 11,
        "domain_entropy": 3.8,
        "vowel_consonant_ratio": 0.1,
        "digit_ratio": 0.3
    })

    outputs = await router.route(record)
    assert len(outputs) == 1
    assert outputs[0].decision == Decision.DETECTION, f"Failed: {outputs[0]}"
    assert outputs[0].detector_id == DetectorId.DNS_DGA_TUNNEL

def test_feature_extraction_reproducibility():
    from app.services.features.mechanisms import extract_dns_lexical_features
    # Exact features for "google.com"
    features = extract_dns_lexical_features("google.com")

    assert features["query_length"] == 10
    assert features["label_count"] == 2
    assert features["max_label_length"] == 6 # "google"
    # Entropy: g:2, o:2, l:1, e:1, .:1, c:1, m:1 (Total 10, 7 unique)
    # Vowels: o, o, e, o (4)
    # Consonants: g, g, l, c, m (5)
    # Digits: 0
    assert features["vowel_consonant_ratio"] == 4.0 / 5.0
    assert features["digit_ratio"] == 0.0
