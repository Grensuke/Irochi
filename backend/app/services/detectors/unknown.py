import uuid
import time
import math
from typing import List

from app.schemas.detectors import (
    DetectorId, ThreatType, Decision, DetectorInput, DetectorOutput, Severity, SourceFeatureReference
)
from app.services.detectors.base import BaseDetector
from app.services.detectors.baseline_state import BaselineStateStore

MIN_SAMPLES = 25
MIN_DEVIATING_SIGNALS = 2
Z_THRESHOLD = 4.5
CONFIDENCE_CUTOFF = 0.55

class UnknownDetector(BaseDetector):
    def __init__(
        self,
        baseline_store: BaselineStateStore,
        min_samples: int = MIN_SAMPLES,
        min_deviating_signals: int = MIN_DEVIATING_SIGNALS,
        z_threshold: float = Z_THRESHOLD,
        confidence_cutoff: float = CONFIDENCE_CUTOFF,
    ):
        self.baseline_store = baseline_store
        self.min_samples = min_samples
        self.min_deviating_signals = min_deviating_signals
        self.z_threshold = z_threshold
        self.confidence_cutoff = confidence_cutoff

    @property
    def detector_id(self) -> DetectorId:
        return DetectorId.UNKNOWN

    @property
    def detector_version(self) -> str:
        return "1.0.0"

    async def evaluate(self, inputs: List[DetectorInput]) -> List[DetectorOutput]:
        """Satisfies the interface but is unused. Called explicitly via evaluate_against_baseline."""
        return []

    async def evaluate_against_baseline(self, inputs: List[DetectorInput], primary_outputs: List[DetectorOutput]) -> List[DetectorOutput]:
        unknown_threat_outputs = []
        
        # Determine the primary decision.
        # Since outputs is 1 per group, we can just check if all are NO_THREAT.
        # Actually, if any output is DETECTION, primary fired.
        primary_fired = any(out.decision == Decision.DETECTION for out in primary_outputs)
        
        for record_input in inputs:
            record = record_input.feature_record
            payload = record.payload.model_dump()
            
            deviating_signals = []
            avg_z = 0.0
            
            # We skip None and non-numeric values
            numeric_fields = {k: v for k, v in payload.items() if isinstance(v, (int, float)) and not isinstance(v, bool) and v is not None}
            
            # If primary fired, we don't alert and we don't update baseline.
            if primary_fired:
                continue

            insufficient_data_signals = 0
            
            field_names = list(numeric_fields.keys())
            if not field_names:
                continue
                
            bulk_stats = await self.baseline_store.bulk_get_stats(
                record.detector_domain.value,
                record.entity_type.value,
                record.entity_key,
                field_names
            )
            
            for field_name, value in numeric_fields.items():
                stats = bulk_stats.get(field_name, {"count": 0.0, "mean": 0.0, "m2": 0.0})
                
                count = stats["count"]
                if count < self.min_samples:
                    insufficient_data_signals += 1
                    continue
                
                mean = stats["mean"]
                m2 = stats["m2"]
                stddev = math.sqrt(m2 / count) if count > 0 else 0.0
                
                if stddev > 0:
                    z = (value - mean) / stddev
                else:
                    z = 0.0 if value == mean else float('inf')
                    
                if abs(z) >= self.z_threshold:
                    deviating_signals.append({
                        "signal_name": field_name,
                        "value": float(value),
                        "threshold": self.z_threshold,
                        "triggered": True,
                        "baseline_mean": mean,
                        "baseline_stddev": stddev,
                        "z_score": z
                    })
                    avg_z += abs(z)

            # If enough signals deviate
            if len(deviating_signals) >= self.min_deviating_signals:
                avg_deviation = avg_z / len(deviating_signals)
                confidence = min(1.0, avg_deviation / 10.0) # Scale arbitrarily to 0-1
                
                # Enforce confidence cutoff so noisy, low-confidence jitter does not flood alerts
                if confidence >= self.confidence_cutoff:
                    severity_candidate = Severity.HIGH if avg_deviation > 7.0 else Severity.MEDIUM

                    evidence = {
                        "message": "Significant deviation from historical baseline",
                        "signals": deviating_signals,
                        "alert_context": {
                            "src_ip": record.entity_key if record.entity_type.value == "source" else None
                        }
                    }
                    
                    unknown_threat_outputs.append(
                        DetectorOutput(
                            output_id=str(uuid.uuid4()),
                            detector_id=self.detector_id,
                            input_id=record_input.input_id,
                            entity_type=record.entity_type,
                            entity_key=record.entity_key,
                            evaluated_at=int(time.time() * 1000000),
                            detector_version="1.0.0",
                            decision=Decision.DETECTION,
                            threat_type=ThreatType.UNKNOWN_THREAT,
                            confidence=confidence,
                            score=confidence * 100,
                            severity_candidate=severity_candidate,
                            evidence=evidence,
                            source_feature_references=[
                                SourceFeatureReference(feature_id=record.feature_id, revision=record.revision)
                            ]
                        )
                    )
                else:
                    # Deviation was below confidence cutoff (normal operational jitter).
                    # Safely absorb into baseline so the baseline learns natural variance.
                    fields_to_update = {k: float(v) for k, v in numeric_fields.items()}
                    await self.baseline_store.bulk_update_stats(
                        record.detector_domain.value,
                        record.entity_type.value,
                        record.entity_key,
                        fields_to_update
                    )
            else:
                # Primary was NO_THREAT, and we did not fire Anomaly. Safe to update baseline for all numeric fields.
                fields_to_update = {k: float(v) for k, v in numeric_fields.items()}
                await self.baseline_store.bulk_update_stats(
                    record.detector_domain.value,
                    record.entity_type.value,
                    record.entity_key,
                    fields_to_update
                )
                    
        return unknown_threat_outputs
