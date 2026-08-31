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
from app.schemas.features import ReconFeatureRecord
from app.services.detectors.base import BaseDetector

class ReconDetector(BaseDetector):
    """
    Initial Recon Detector for Irochi MVP.
    Uses a deterministic rule-based / statistical baseline.
    Evaluates 'unique_destination_ports' produced by WP-D Tumbling Window.
    """
    def __init__(self, portscan_threshold: int = 50):
        # DEVELOPMENT CONFIG ONLY: Open parameter.
        self.portscan_threshold = portscan_threshold
        self._version = "1.0.0"

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

            # WP-E Validation ensures we only receive compatible records (ReconFeatureRecord).
            if not isinstance(record, ReconFeatureRecord):
                outputs.append(self._create_output(
                    inp, Decision.INVALID_INPUT, evidence={"reason": "Expected ReconFeatureRecord"}
                ))
                continue

            unique_ports = record.payload.unique_destination_ports

            # Missing != Zero Behavior
            if unique_ports is None:
                outputs.append(self._create_output(
                    inp, Decision.INSUFFICIENT_DATA, evidence={"reason": "unique_destination_ports is missing"}
                ))
                continue

            # Deterministic Threshold Evaluation
            if unique_ports > self.portscan_threshold:
                decision = Decision.DETECTION
            else:
                decision = Decision.NO_THREAT

            evidence = {
                "feature": "unique_destination_ports",
                "observed": unique_ports,
                "threshold": self.portscan_threshold,
                "rule": "unique_destination_ports > threshold"
            }

            outputs.append(self._create_output(
                inp, decision, score=float(unique_ports), evidence=evidence
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
            detector_id=DetectorId.RECON,
            input_id=inp.input_id,
            entity_type=record.entity_type,
            entity_key=record.entity_key,
            evaluated_at=int(time.time() * 1000000),
            detector_version=self.detector_version,
            decision=decision,
            threat_type=ThreatType.RECON_PORTSCAN, # Must be populated as specified
            score=score,
            confidence=None,           # Do not invent confidence semantics for a deterministic rule
            severity_candidate=None,   # Severity mapping remains outside the detector's policy
            evidence=evidence,
            source_feature_references=[
                SourceFeatureReference(feature_id=record.feature_id, revision=record.revision)
            ]
        )
