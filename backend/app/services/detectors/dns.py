import os
import json
import logging
from typing import Optional, Any
from app.schemas.detectors import (
    DetectorId,
    ThreatType,
    Decision,
    DetectorInput,
    DetectorOutput,
    SourceFeatureReference
)
from app.services.detectors.base import BaseDetector
from app.schemas.features import DnsFeatureRecord

logger = logging.getLogger(__name__)

class DnsDetector(BaseDetector):
    def __init__(self):
        super().__init__()
        self.model = None
        self.metadata = None
        self.threshold = 0.80 # Default, might be overridden by metadata
        self._load_model()

    def _load_model(self):
        """Loads the model artifact outside the git repo."""
        model_path = os.getenv("IROCHI_DGA_MODEL_PATH", r"C:\Users\STARK\Documents\Irochi-Data\models\dns_dga_model_v1.joblib")
        meta_path = model_path.replace(".joblib", ".meta.json")

        try:
            import joblib
            if os.path.exists(model_path) and os.path.exists(meta_path):
                self.model = joblib.load(model_path)
                with open(meta_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)

                # Development/MVP Threshold Override from Metadata
                if "threshold" in self.metadata:
                    self.threshold = self.metadata["threshold"]

                logger.info(f"Successfully loaded DGA model {self.metadata.get('model_version')} from {model_path}")
            else:
                logger.error(f"DGA model or metadata not found at {model_path}")
        except Exception as e:
            logger.error(f"Failed to load DGA model: {e}", exc_info=True)

    @property
    def detector_id(self) -> DetectorId:
        return DetectorId.DNS_DGA_TUNNEL

    @property
    def detector_version(self) -> str:
        return self.metadata.get("model_version", "v1.0.0") if self.metadata else "v1.0.0"

    @property
    def supported_threats(self) -> list[ThreatType]:
        return [ThreatType.DGA_DNS_TUNNEL]

    async def evaluate(self, inputs: list[DetectorInput]) -> list[DetectorOutput]:
        import uuid
        import time
        import numpy as np

        results = []
        for input_data in inputs:
            envelope = {
                "output_id": str(uuid.uuid4()),
                "input_id": input_data.input_id,
                "detector_id": self.detector_id,
                "detector_version": self.detector_version,
                "evaluated_at": int(time.time()),
                "threat_type": ThreatType.DGA_DNS_TUNNEL,
                "entity_type": input_data.feature_record.entity_type,
                "entity_key": input_data.feature_record.entity_key,
                "decision": Decision.NO_THREAT,
                "score": 0.0,
                "confidence": None,
                "severity_candidate": None,
                "evidence": {},
                "source_feature_references": [
                    SourceFeatureReference(
                        feature_id=input_data.feature_record.feature_id,
                        revision=input_data.feature_record.revision
                    )
                ]
            }

            # Handle model load failures
            if not self.model or not self.metadata:
                envelope["decision"] = Decision.DETECTOR_ERROR
                envelope["evidence"] = {"error": "Model artifact not loaded or missing."}
                results.append(DetectorOutput(**envelope))
                continue

            # Validate input schema
            if not isinstance(input_data.feature_record, DnsFeatureRecord):
                logger.error(f"DnsDetector received invalid record type: {type(input_data.feature_record)}")
                envelope["decision"] = Decision.INVALID_INPUT
                results.append(DetectorOutput(**envelope))
                continue

            payload = input_data.feature_record.payload

            # Handle missing domains
            if payload.query_length is None or payload.query_length == 0:
                envelope["decision"] = Decision.INSUFFICIENT_DATA
                envelope["evidence"] = {"reason": "missing query_length or empty domain"}
                results.append(DetectorOutput(**envelope))
                continue

            # Handle malformed (missing features that are expected)
            features_expected = self.metadata.get("feature_order", [])
            feature_vector = []
            malformed = False
            for feat in features_expected:
                val = getattr(payload, feat, None)
                if val is None:
                    envelope["decision"] = Decision.INVALID_INPUT
                    envelope["evidence"] = {"reason": f"missing feature {feat}"}
                    results.append(DetectorOutput(**envelope))
                    malformed = True
                    break
                feature_vector.append(val)

            if malformed:
                continue

            # Inference
            try:
                X = np.array([feature_vector])
                prob = float(self.model.predict_proba(X)[0][1])

                envelope["score"] = prob
                envelope["evidence"] = {
                    "probability": prob,
                    "threshold": self.threshold,
                    "model_version": self.metadata.get("model_version", "unknown"),
                    "features_used": dict(zip(features_expected, feature_vector))
                }

                if prob > self.threshold:
                    envelope["decision"] = Decision.DETECTION

            except Exception as e:
                logger.error(f"Inference error in DnsDetector: {e}", exc_info=True)
                envelope["decision"] = Decision.DETECTOR_ERROR
                envelope["evidence"] = {"error": f"Inference exception: {str(e)}"}

            results.append(DetectorOutput(**envelope))

        return results
