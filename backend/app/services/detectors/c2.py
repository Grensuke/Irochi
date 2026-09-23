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
from app.schemas.features import TlsC2FeatureRecord

logger = logging.getLogger(__name__)

class C2Detector(BaseDetector):
    def __init__(self):
        super().__init__()
        # Configurable parameters for multi-signal C2 scoring
        self.min_connection_frequency = 5.0    # 5 connections per window
        self.min_timing_regularity = 0.5       # Moderate regularity
        self.max_jitter = 0.5                  # Low relative variance
        
        self.weights = {
            "frequency": 0.3,
            "regularity": 0.3,
            "jitter": 0.2,
            "blacklist": 0.2
        }
        
        self.confidence_cutoff = 0.60
        self.min_triggers = 2

    @property
    def detector_id(self) -> DetectorId:
        return DetectorId.TLS_C2

    @property
    def detector_version(self) -> str:
        return "v1.0.0"

    @property
    def supported_threats(self) -> List[ThreatType]:
        return [ThreatType.C2_BEACONING]

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
                "threat_type": ThreatType.C2_BEACONING,
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

            if not isinstance(input_data.feature_record, TlsC2FeatureRecord):
                logger.error(f"C2Detector received invalid record type: {type(input_data.feature_record)}")
                envelope["decision"] = Decision.INVALID_INPUT
                results.append(DetectorOutput(**envelope))
                continue

            payload = input_data.feature_record.payload

            # Require core temporal fields
            if payload.connection_frequency is None or payload.timing_regularity is None or payload.jitter is None:
                envelope["decision"] = Decision.INSUFFICIENT_DATA
                envelope["evidence"] = {"reason": "missing connection_frequency, timing_regularity, or jitter"}
                results.append(DetectorOutput(**envelope))
                continue

            signals_evaluated = []
            score_total = 0.0
            triggers = 0
            
            # 1. Frequency
            freq_val = payload.connection_frequency
            freq_score = min(freq_val / self.min_connection_frequency, 1.2) if freq_val > 0 else 0
            is_freq_triggered = freq_val >= self.min_connection_frequency
            if is_freq_triggered: triggers += 1
            signals_evaluated.append({
                "signal_name": "connection_frequency",
                "value": freq_val,
                "threshold": self.min_connection_frequency,
                "normalized_score": freq_score,
                "triggered": is_freq_triggered
            })
            score_total += freq_score * self.weights["frequency"]

            # 2. Regularity
            reg_val = payload.timing_regularity
            reg_score = min(reg_val / self.min_timing_regularity, 1.2) if reg_val > 0 else 0
            is_reg_triggered = reg_val >= self.min_timing_regularity
            if is_reg_triggered: triggers += 1
            
            signals_evaluated.append({
                "signal_name": "timing_regularity",
                "value": reg_val,
                "threshold": self.min_timing_regularity,
                "normalized_score": reg_score,
                "triggered": is_reg_triggered
            })
            score_total += reg_score * self.weights["regularity"]
            
            # 3. Jitter
            jitter_val = payload.jitter
            jitter_score = 0
            is_jitter_triggered = False
            if jitter_val <= self.max_jitter:
                jitter_score = min(1.0 + (self.max_jitter - jitter_val) / self.max_jitter, 1.2)
                is_jitter_triggered = True
                triggers += 1
            
            signals_evaluated.append({
                "signal_name": "jitter",
                "value": jitter_val,
                "threshold": self.max_jitter,
                "normalized_score": jitter_score,
                "triggered": is_jitter_triggered
            })
            score_total += jitter_score * self.weights["jitter"]
            
            # 4. Blacklist Match (Optional but strong)
            bl_val = getattr(payload, 'ja3_blacklist_match', False)
            bl_score = 1.5 if bl_val else 0.0
            is_bl_triggered = bool(bl_val)
            if is_bl_triggered: triggers += 1
            signals_evaluated.append({
                "signal_name": "ja3_blacklist_match",
                "value": bl_val,
                "threshold": True,
                "normalized_score": bl_score,
                "triggered": is_bl_triggered
            })
            score_total += bl_score * self.weights["blacklist"]
            
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
                if confidence >= 0.85:
                    envelope["severity_candidate"] = Severity.CRITICAL
                elif confidence >= 0.70:
                    envelope["severity_candidate"] = Severity.HIGH
                else:
                    envelope["severity_candidate"] = Severity.MEDIUM

            results.append(DetectorOutput(**envelope))

        return results
