"""Exfiltration Model — XGBoost classifier wrapper with rule-based fallback.

Predicts exfiltration probability from 6 derived network features.
"""

from __future__ import annotations

from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

MODEL_PATH = Path(__file__).parent / "saved" / "exfil.joblib"


class ExfilModel:
    """XGBoost exfiltration classifier with rule-based fallback."""

    def __init__(self) -> None:
        self._model = None
        self._loaded = False

    def load(self) -> None:
        """Load the joblib model file. Logs if not found."""
        try:
            import joblib
            if MODEL_PATH.exists():
                self._model = joblib.load(MODEL_PATH)
                logger.info("exfil_model_loaded", path=str(MODEL_PATH))
            else:
                logger.warning("exfil_model_not_found_using_rules", path=str(MODEL_PATH))
            self._loaded = True
        except Exception as exc:
            logger.error("exfil_model_load_failed", error=str(exc))
            self._loaded = True

    def predict_proba(self, features: list[float]) -> float:
        """Predict exfiltration probability from 6-feature vector.

        Features:
            0. outbound_inbound_ratio
            1. rolling_transfer_bytes (orig_total)
            2. byte_rate_orig_bps
            3. duration_seconds
            4. dst_port_risk_flag (0 or 1)
            5. is_encrypted (0 or 1)

        If model loaded: use XGBoost predict_proba.
        If not loaded: rule-based fallback (max 0.85).
        """
        if self._model is not None:
            try:
                import numpy as np
                X = np.array([features])
                proba = self._model.predict_proba(X)[0][1]
                return float(proba)
            except Exception as exc:
                logger.warning("exfil_prediction_failed_using_rules", error=str(exc))

        # Rule-based fallback
        ratio = features[0]
        orig_total = features[1]
        orig_bps = features[2]
        dst_port_risk = features[4]

        score = 0.0
        if ratio > 10.0:
            score += 0.25
        if ratio > 50.0:
            score += 0.15
        if orig_total > 524_288_000:  # 500MB
            score += 0.20
        if orig_bps > 52_428_800:  # 50 MB/s
            score += 0.15
        if dst_port_risk:
            score += 0.10

        return min(score, 0.85)
