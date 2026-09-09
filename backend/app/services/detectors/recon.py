import uuid
import time
from typing import List, Optional, Dict, Any

from app.schemas.detectors import (
    DetectorId,
    DetectorInput,
    DetectorOutput,
    Decision,
    ThreatType,
    SourceFeatureReference,
)
from app.schemas.features import ReconFeatureRecord
from app.services.detectors.base import BaseDetector

class ReconDetector(BaseDetector):
    """
    Context-Aware Recon Detector for Irochi.
    Evaluates unique_destination_ports, unique_destination_hosts,
    scan_rate, and connection_fan_out using a multi-signal weighted scoring model.
    """
    def __init__(
        self,
        thresholds: Optional[Dict[str, float]] = None,
        weights: Optional[Dict[str, float]] = None,
        min_triggers: int = 1,
        confidence_cutoff: float = 0.60
    ):
        # INITIAL / UNVALIDATED Defaults based on design baseline
        self.thresholds = thresholds or {
            "unique_destination_ports": 50.0,
            "unique_destination_hosts": 50.0,
            "scan_rate": 10.0,
            "connection_fan_out": 0.5,
        }
        self.weights = weights or {
            "unique_destination_ports": 0.40,
            "unique_destination_hosts": 0.10,
            "scan_rate": 0.40,
            "connection_fan_out": 0.10,
        }
        self.min_triggers = min_triggers
        self.confidence_cutoff = confidence_cutoff
        self._version = "2.0.0"

    @property
    def detector_id(self) -> DetectorId:
        return DetectorId.RECON

    @property
    def detector_version(self) -> str:
        return self._version

    async def evaluate(self, inputs: List[DetectorInput]) -> List[DetectorOutput]:
        outputs = []
        for inp in inputs:
            record = inp.feature_record

            if not isinstance(record, ReconFeatureRecord):
                outputs.append(self._create_output(
                    inp, Decision.INVALID_INPUT, evidence={"reason": "Expected ReconFeatureRecord"}
                ))
                continue

            signals = {
                "unique_destination_ports": record.payload.unique_destination_ports,
                "unique_destination_hosts": record.payload.unique_destination_hosts,
                "scan_rate": record.payload.scan_rate,
                "connection_fan_out": record.payload.connection_fan_out,
            }

            # Safely handle missing optional fields
            if signals["unique_destination_ports"] is None:
                outputs.append(self._create_output(
                    inp, Decision.INSUFFICIENT_DATA, evidence={"reason": "unique_destination_ports is missing"}
                ))
                continue

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
            detector_id=DetectorId.RECON,
            input_id=inp.input_id,
            entity_type=record.entity_type,
            entity_key=record.entity_key,
            evaluated_at=int(time.time() * 1000000),
            detector_version=self.detector_version,
            decision=decision,
            threat_type=ThreatType.RECON_PORTSCAN,
            score=score,
            confidence=confidence,
            severity_candidate=None,
            evidence=evidence,
            source_feature_references=[
                SourceFeatureReference(feature_id=record.feature_id, revision=record.revision)
            ]
        )
