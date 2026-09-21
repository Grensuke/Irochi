import uuid
import time
import pickle
import logging
from typing import List, Optional, Dict, Any

try:
    from river import anomaly
    HAS_RIVER = True
except ImportError:
    HAS_RIVER = False

logger = logging.getLogger(__name__)

from app.schemas.detectors import (
    DetectorId,
    DetectorInput,
    DetectorOutput,
    Decision,
    ThreatType,
    SourceFeatureReference,
)
from app.schemas.features import DdosFeatureRecord
from app.services.detectors.base import BaseDetector

class DdosDetector(BaseDetector):
    """
    Context-Aware DDoS Detector for Irochi.
    Evaluates packet_rate, byte_rate, syn_ratio, and source diversity
    using a multi-signal weighted scoring model.
    """
    def __init__(
        self,
        thresholds: Optional[Dict[str, float]] = None,
        weights: Optional[Dict[str, float]] = None,
        min_triggers: int = 1,
        confidence_cutoff: float = 0.60,
        redis_service: Any = None
    ):
        # INITIAL / UNVALIDATED Defaults based on design baseline
        self.thresholds = thresholds or {
            "packet_rate": 500.0,
            "byte_rate": 50000.0,
            "syn_ratio": 0.70,
            "source_ip_entropy": 2.0,
            "anomaly_score": 0.80,
        }
        self.weights = weights or {
            "packet_rate": 0.30,
            "syn_ratio": 0.10,
            "source_ip_entropy": 0.30,
            "byte_rate": 0.10,
            "anomaly_score": 0.20,
        }
        self.min_triggers = min_triggers
        self.confidence_cutoff = confidence_cutoff
        self.redis_service = redis_service
        self._version = "2.0.0"

    @property
    def detector_id(self) -> DetectorId:
        return DetectorId.DDOS

    @property
    def detector_version(self) -> str:
        return self._version

    async def evaluate(self, inputs: List[DetectorInput]) -> List[DetectorOutput]:
        outputs = []
        for inp in inputs:
            record = inp.feature_record

            if not isinstance(record, DdosFeatureRecord):
                outputs.append(self._create_output(
                    inp, Decision.INVALID_INPUT, evidence={"reason": "Expected DdosFeatureRecord"}
                ))
                continue

            signals = {
                "packet_rate": record.payload.packet_rate,
                "byte_rate": record.payload.byte_rate,
                "syn_ratio": record.payload.syn_ratio,
                "source_ip_entropy": record.payload.source_ip_entropy,
            }

            # Safely handle missing optional fields
            if signals["packet_rate"] is None:
                outputs.append(self._create_output(
                    inp, Decision.INSUFFICIENT_DATA, evidence={"reason": "packet_rate is missing"}
                ))
                continue

            anomaly_score = 0.0
            if HAS_RIVER and self.redis_service and self.redis_service._client:
                key = f"irochi:anomaly:river:ddos:{record.entity_key}"
                model = None
                try:
                    data = await self.redis_service._client.get(key)
                    if data:
                        model = pickle.loads(bytes.fromhex(data))
                except Exception as e:
                    logger.warning(f"Failed to load river model from redis: {e}")

                if model is None:
                    model = anomaly.HalfSpaceTrees(
                        n_trees=25,
                        height=10,
                        window_size=250,
                        seed=42
                    )

                features = {
                    "packet_rate": float(signals["packet_rate"] or 0),
                    "byte_rate": float(signals["byte_rate"] or 0),
                    "syn_ratio": float(signals["syn_ratio"] or 0),
                    "source_ip_entropy": float(signals["source_ip_entropy"] or 0)
                }

                try:
                    anomaly_score = model.score_one(features)
                    model.learn_one(features)
                    hex_data = pickle.dumps(model).hex()
                    await self.redis_service._client.set(key, hex_data)
                except Exception as e:
                    logger.warning(f"Failed to score/save river model: {e}")
                    anomaly_score = 0.0
                    
            signals["anomaly_score"] = anomaly_score

            scores = {}
            evidence_items = []

            for name, val in signals.items():
                if val is not None:
                    thresh = self.thresholds.get(name, 1.0)
                    score = min(val / thresh, 1.0) if thresh > 0 else 0.0
                    scores[name] = score
                    evidence_items.append({
                        "signal_name": name,
                        "value": round(val, 4) if isinstance(val, float) else val,
                        "threshold": thresh,
                        "triggered": score >= 0.5
                    })
                else:
                    scores[name] = 0.0

            confidence = sum(self.weights.get(s, 0.0) * scores[s] for s in scores)
            confidence = min(confidence, 1.0)

            triggered_count = sum(1 for v in scores.values() if v >= 0.5)

            if triggered_count >= self.min_triggers and confidence > self.confidence_cutoff:
                decision = Decision.DETECTION
            else:
                decision = Decision.NO_THREAT

            evidence = {
                "signals": evidence_items,
                "triggered_count": triggered_count,
                "min_triggers": self.min_triggers,
                "confidence_cutoff": self.confidence_cutoff
            }

            outputs.append(self._create_output(
                inp, decision, score=float(confidence), confidence=float(confidence), evidence=evidence
            ))

        return outputs

    def _create_output(
        self,
        inp: DetectorInput,
        decision: Decision,
        score: Optional[float] = None,
        confidence: Optional[float] = None,
        evidence: Optional[dict] = None
    ) -> DetectorOutput:
        record = inp.feature_record
        return DetectorOutput(
            output_id=str(uuid.uuid4()),
            detector_id=DetectorId.DDOS,
            input_id=inp.input_id,
            entity_type=record.entity_type,
            entity_key=record.entity_key,
            evaluated_at=int(time.time() * 1000000),
            detector_version=self.detector_version,
            decision=decision,
            threat_type=ThreatType.VOLUMETRIC_DDOS,
            score=score,
            confidence=confidence,
            severity_candidate=None,
            evidence=evidence,
            source_feature_references=[
                SourceFeatureReference(feature_id=record.feature_id, revision=record.revision)
            ]
        )
