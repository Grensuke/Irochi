import uuid
import time
from typing import List, Optional

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
    Initial DDoS Detector for Irochi MVP.
    Evaluates 'packet_rate' produced by WP-D Tumbling/Sliding Window.
    """
    def __init__(self, packet_rate_threshold: float = 1000.0):
        # DEVELOPMENT CONFIG ONLY: Open parameter.
        self.packet_rate_threshold = packet_rate_threshold
        self._version = "1.0.0"

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

            # WP-E Validation ensures we only receive compatible records.
            if not isinstance(record, DdosFeatureRecord):
                outputs.append(self._create_output(
                    inp, Decision.INVALID_INPUT, evidence={"reason": "Expected DdosFeatureRecord"}
                ))
                continue

            packet_rate = record.payload.packet_rate

            # Missing != Zero Behavior
            if packet_rate is None:
                outputs.append(self._create_output(
                    inp, Decision.INSUFFICIENT_DATA, evidence={"reason": "packet_rate is missing"}
                ))
                continue

            # Deterministic Threshold Evaluation
            if packet_rate > self.packet_rate_threshold:
                decision = Decision.DETECTION
            else:
                decision = Decision.NO_THREAT

            evidence = {
                "feature": "packet_rate",
                "observed": packet_rate,
                "threshold": self.packet_rate_threshold,
                "rule": "packet_rate > threshold"
            }

            outputs.append(self._create_output(
                inp, decision, score=float(packet_rate), evidence=evidence
            ))

        return outputs

    def _create_output(
        self,
        inp: DetectorInput,
        decision: Decision,
        score: Optional[float] = None,
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
            confidence=None,
            severity_candidate=None,
            evidence=evidence,
            source_feature_references=[
                SourceFeatureReference(feature_id=record.feature_id, revision=record.revision)
            ]
        )
