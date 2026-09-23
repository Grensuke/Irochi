import os
import json
import uuid
import time
import logging
from typing import List
import numpy as np

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
            "ratio": 0.33,
            "rate": 0.33,
            "ml_anomaly": 0.34
        }
        
        self.confidence_cutoff = 0.60
        self.min_triggers = 2

        self.model = None
        self.metadata = None
        self.ml_threshold = 0.5
        self._load_model()

    def _load_model(self):
        from app.core.config import VIBHINETRA_EXFIL_MODEL_PATH
        model_path = VIBHINETRA_EXFIL_MODEL_PATH
        meta_path = model_path.replace(".joblib", ".meta.json")

        try:
            import joblib
            import xgboost # Check if installed
            if os.path.exists(model_path) and os.path.exists(meta_path):
                self.model = joblib.load(model_path)
                with open(meta_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                
                if "threshold" in self.metadata:
                    self.ml_threshold = self.metadata["threshold"]
                    
                logger.info(f"Successfully loaded XGBoost Exfiltration model from {model_path}")
            else:
                logger.error(f"XGBoost Exfiltration model or metadata not found at {model_path}")
        except Exception as e:
            logger.error(f"Failed to load XGBoost Exfiltration model: {e}", exc_info=True)

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

            # 3. XGBoost Model (ML Anomaly)
            ml_prob = 0.0
            is_ml_triggered = False
            if self.model:
                try:
                    features = [ratio_val, rate_val] # order matching train_exfil_model.py
                    X = np.array([features])
                    ml_prob = float(self.model.predict_proba(X)[0][1])
                    if ml_prob >= self.ml_threshold:
                        is_ml_triggered = True
                        triggers += 1
                except Exception as e:
                    logger.error(f"Inference error in ExfiltrationDetector: {e}")

            signals_evaluated.append({
                "signal_name": "ml_anomaly",
                "value": ml_prob,
                "threshold": self.ml_threshold,
                "normalized_score": ml_prob,
                "triggered": is_ml_triggered
            })
            score_total += ml_prob * self.weights["ml_anomaly"]
            
            # No volume in payload schema for MVP, use ratio, rate, and ML model.
            
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
