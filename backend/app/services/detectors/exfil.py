import uuid
import time
import logging
from typing import List

from app.schemas.detectors import (
    DetectorId,
    ThreatType,
    Decision,
    DetectorInput,
    DetectorOutput,
    SourceFeatureReference,
    Severity
)
from app.services.detectors.base import BaseDetector
from app.schemas.features import ExfilFeatureRecord

logger = logging.getLogger(__name__)

class ExfiltrationDetector(BaseDetector):
    def __init__(self):
        super().__init__()
        self.min_ratio_threshold = 3.0                
        self.min_byte_rate_threshold = 50_000          # 50 KB/s
        
        self.weights = {
            "ratio": 0.5,
            "rate": 0.5
        }
        
        self.confidence_cutoff = 0.60
        self.min_triggers = 2

    @property
    def detector_id(self) -> DetectorId:
        return DetectorId.EXFILTRATION

    @property
    def detector_version(self) -> str:
        return "v1.0.0"

    @property
    def supported_threats(self) -> List[ThreatType]:
        return [ThreatType.DATA_EXFILTRATION]

    async def evaluate(self, inputs: List[DetectorInput]) -> List[DetectorOutput]:
        results = []
        for input_data in inputs:
            envelope = {
                "output_id": str(uuid.uuid4()),
                "input_id": input_data.input_id,
                "detector_id": self.detector_id,
                "detector_version": self.detector_version,
                "evaluated_at": int(time.time() * 1_000_000),
                "entity_type": input_data.feature_record.entity_type,
                "entity_key": input_data.feature_record.entity_key,
                "decision": Decision.NO_THREAT,
                "threat_type": ThreatType.DATA_EXFILTRATION,
                "score": 0.0,
                "confidence": 0.0,
                "severity_candidate": None,
                "evidence": {},
                "source_feature_references": [
                    SourceFeatureReference(
                        feature_id=input_data.feature_record.feature_id,
                        revision=input_data.feature_record.revision
                    )
                ]
            }

            if not isinstance(input_data.feature_record, ExfilFeatureRecord):
                logger.error(f"ExfiltrationDetector received invalid record type: {type(input_data.feature_record)}")
                envelope["decision"] = Decision.INVALID_INPUT
                results.append(DetectorOutput(**envelope))
                continue

            payload = input_data.feature_record.payload

            # Require core fields
            if payload.outbound_inbound_ratio is None or payload.byte_rate is None:
                envelope["decision"] = Decision.INSUFFICIENT_DATA
                envelope["evidence"] = {"reason": "missing outbound_inbound_ratio or byte_rate"}
                results.append(DetectorOutput(**envelope))
                continue

            
            signals_evaluated = []
            score_total = 0.0
            triggers = 0
            
            # 1. Ratio
            ratio_val = payload.outbound_inbound_ratio
            ratio_score = min(ratio_val / self.min_ratio_threshold, 1.5) if ratio_val > 0 else 0
            is_ratio_triggered = ratio_val >= self.min_ratio_threshold
            if is_ratio_triggered: triggers += 1
            signals_evaluated.append({
                "signal_name": "outbound_inbound_ratio",
                "value": ratio_val,
                "threshold": self.min_ratio_threshold,
                "normalized_score": ratio_score,
                "triggered": is_ratio_triggered
            })
            score_total += ratio_score * self.weights["ratio"]

            # 2. Rate
            rate_val = payload.byte_rate
            rate_score = min(rate_val / self.min_byte_rate_threshold, 1.5) if rate_val > 0 else 0
            is_rate_triggered = rate_val >= self.min_byte_rate_threshold
            if is_rate_triggered: triggers += 1
            signals_evaluated.append({
                "signal_name": "byte_rate",
                "value": rate_val,
                "threshold": self.min_byte_rate_threshold,
                "normalized_score": rate_score,
                "triggered": is_rate_triggered
            })
            score_total += rate_score * self.weights["rate"]
            
            # No volume in payload schema for MVP, use ratio and rate.
            
            confidence = min(score_total, 1.0)
            
            envelope["score"] = score_total
            envelope["confidence"] = confidence
            envelope["evidence"] = {
                "signals": signals_evaluated,
                "triggered_count": triggers,
                "min_triggers": self.min_triggers,
                "confidence_cutoff": self.confidence_cutoff
            }

            if confidence >= self.confidence_cutoff and triggers >= self.min_triggers:
                envelope["decision"] = Decision.DETECTION
                if confidence > 0.9:
                    envelope["severity_candidate"] = Severity.CRITICAL
                elif confidence > 0.75:
                    envelope["severity_candidate"] = Severity.HIGH
                else:
                    envelope["severity_candidate"] = Severity.MEDIUM

            results.append(DetectorOutput(**envelope))

        return results
