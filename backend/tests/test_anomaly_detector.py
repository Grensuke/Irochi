import pytest
import uuid
from app.services.detectors.anomaly import AnomalyDetector
from app.services.detectors.baseline_state import BaselineStateStore
from app.schemas.detectors import (
    DetectorInput, 
    DetectorOutput, 
    Decision, 
    ThreatType,
    DetectorId,
    SourceFeatureReference
)
from app.schemas.features import (
    DdosFeatureRecord,
    DetectorDomain,
    EntityType,
    FeatureMechanism,
    DdosFeaturePayload
)

class MockBaselineStore:
    def __init__(self):
        self.stats = {}
    
    async def get_stats(self, domain, entity_type, entity_key, field_name):
        key = (domain, entity_type, entity_key, field_name)
        if key not in self.stats:
            return {"count": 0, "mean": 0.0, "m2": 0.0, "min": float('inf'), "max": float('-inf')}
        return self.stats[key]
        
    async def update_stats(self, domain, entity_type, entity_key, field_name, value):
        key = (domain, entity_type, entity_key, field_name)
        if key not in self.stats:
            self.stats[key] = {"count": 0, "mean": 0.0, "m2": 0.0, "min": float('inf'), "max": float('-inf')}
        stats = self.stats[key]
        count = stats["count"]
        mean = stats["mean"]
        stats["count"] += 1
        delta = value - mean
        stats["mean"] += delta / stats["count"]
        delta2 = value - stats["mean"]
        stats["m2"] += delta * delta2
        stats["min"] = min(stats["min"], value)
        stats["max"] = max(stats["max"], value)

@pytest.mark.asyncio
async def test_baseline_not_updated_during_known_attack():
    store = MockBaselineStore()
    detector = AnomalyDetector(store)
    
    # Pre-populate some baseline to simulate existing stats
    key = ("ddos", "source", "192.168.1.100", "packet_rate")
    store.stats[key] = {"count": 25, "mean": 100.0, "m2": 500.0, "min": 50.0, "max": 150.0}
    
    record = DdosFeatureRecord(
        feature_id=str(uuid.uuid4()),
        mechanism=FeatureMechanism.WINDOWED,
        detector_domain=DetectorDomain.DDOS,
        entity_type=EntityType.SOURCE,
        entity_key="192.168.1.100",
        computed_at=12345,
        schema_version="1.0",
        revision=1,
        payload=DdosFeaturePayload(packet_rate=5000) # massive spike
    )
    inputs = [DetectorInput(input_id=str(uuid.uuid4()), detector_id=DetectorId.ANOMALY, feature_record=record)]
    
    primary_outputs = [
        DetectorOutput(
            output_id=str(uuid.uuid4()),
            input_id=inputs[0].input_id,
            detector_id=DetectorId.DDOS,
            entity_type=EntityType.SOURCE,
            entity_key="192.168.1.100",
            detector_version="1.0.0",
            evaluated_at=12345,
            decision=Decision.DETECTION,
            threat_type=ThreatType.VOLUMETRIC_DDOS,
            score=99.0,
            source_feature_references=[
                SourceFeatureReference(feature_id=record.feature_id, revision=record.revision)
            ]
        )
    ]
    
    before_stats = dict(store.stats[key])
    
    outputs = await detector.evaluate_against_baseline(inputs, primary_outputs)
    
    after_stats = store.stats[key]
    
    assert outputs == [], "Anomaly detector should not fire if primary already fired"
    assert before_stats == after_stats, "Baseline should not be updated when primary detects attack"

@pytest.mark.asyncio
async def test_baseline_not_updated_during_active_anomaly():
    store = MockBaselineStore()
    detector = AnomalyDetector(store)
    
    # Pre-populate
    key1 = ("ddos", "source", "192.168.1.100", "packet_rate")
    key2 = ("ddos", "source", "192.168.1.100", "byte_rate")
    
    store.stats[key1] = {"count": 25, "mean": 100.0, "m2": 10.0, "min": 50.0, "max": 150.0}
    store.stats[key2] = {"count": 25, "mean": 1000.0, "m2": 100.0, "min": 500.0, "max": 1500.0}
    
    record = DdosFeatureRecord(
        feature_id=str(uuid.uuid4()),
        mechanism=FeatureMechanism.WINDOWED,
        detector_domain=DetectorDomain.DDOS,
        entity_type=EntityType.SOURCE,
        entity_key="192.168.1.100",
        computed_at=12345,
        schema_version="1.0",
        revision=1,
        payload=DdosFeaturePayload(packet_rate=9999, byte_rate=99999) # anomalies
    )
    inputs = [DetectorInput(input_id=str(uuid.uuid4()), detector_id=DetectorId.ANOMALY, feature_record=record)]
    
    # Primary output says NO_THREAT
    primary_outputs = [
        DetectorOutput(
            output_id=str(uuid.uuid4()),
            input_id=inputs[0].input_id,
            detector_id=DetectorId.DDOS,
            entity_type=EntityType.SOURCE,
            entity_key="192.168.1.100",
            detector_version="1.0.0",
            evaluated_at=12345,
            decision=Decision.NO_THREAT,
            threat_type=ThreatType.VOLUMETRIC_DDOS,
            score=1.0,
            source_feature_references=[
                SourceFeatureReference(feature_id=record.feature_id, revision=record.revision)
            ]
        )
    ]
    
    before_stats1 = dict(store.stats[key1])
    before_stats2 = dict(store.stats[key2])
    
    outputs = await detector.evaluate_against_baseline(inputs, primary_outputs)
    
    after_stats1 = store.stats.get(key1)
    after_stats2 = store.stats.get(key2)
    
    assert len(outputs) == 1
    assert outputs[0].decision == Decision.DETECTION
    assert before_stats1 == after_stats1, "Baseline should not be updated when anomaly fires"
    assert before_stats2 == after_stats2, "Baseline should not be updated when anomaly fires"
