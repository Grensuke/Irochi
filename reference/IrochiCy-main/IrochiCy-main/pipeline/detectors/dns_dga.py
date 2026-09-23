"""DNS/DGA Detector — XGBoost classifier on lexical features + frequency checks.

Processes DNS events. Uses ML model for domain generation algorithm detection
with a rule-based fallback when the model is not loaded.
"""

from __future__ import annotations

from typing import Optional

import structlog

from detectors.base import BaseDetector
from detectors.result import DetectorResult, EvidenceItem
from features.redis_state import RedisHotState
from features.windows import SlidingWindowCounter
from models.ml.dns_dga_model import DnsDgaModel

logger = structlog.get_logger(__name__)


class DnsDgaDetector(BaseDetector):
    """DNS/DGA detector using XGBoost + frequency analysis."""

    detector_id = "dns-dga-detector-v1"
    threat_type = "dns_dga"

    def __init__(self) -> None:
        self.model = DnsDgaModel()
        self.model.load()
        self.query_counter = SlidingWindowCounter(60)

    async def process_event(
        self,
        event,
        windows: dict,
        redis_state: RedisHotState,
    ) -> Optional[DetectorResult]:
        """Process a DNS event for DGA indicators."""
        if event.event_type != "dns":
            return None

        src = event.src_ip
        query = event.payload.query
        now = event.timestamp / 1_000_000.0

        # Track query frequency
        self.query_counter.add(src, now, 1)
        query_frequency = self.query_counter.get_count(src, now)

        # Run model
        dga_probability = self.model.predict_proba(query)
        features = self.model.extract_features(query)

        # Frequency trigger
        freq_triggered = query_frequency > 100

        # Fire condition
        if dga_probability <= 0.55 and not freq_triggered:
            return None

        # Confidence
        confidence = dga_probability * 0.75
        if freq_triggered:
            confidence += 0.15
        confidence = min(confidence, 1.0)

        evidence = [
            EvidenceItem(
                signal_name="domain_entropy",
                signal_type="derived",
                value=round(features[0], 4) if features else 0,
                threshold=None,
                triggered=dga_probability > 0.55,
            ),
            EvidenceItem(
                signal_name="n_gram_score",
                signal_type="derived",
                value=round(features[6], 4) if len(features) > 6 else 0,
                threshold=None,
                triggered=dga_probability > 0.55,
            ),
            EvidenceItem(
                signal_name="query_length",
                signal_type="raw",
                value=len(query),
                threshold=None,
                triggered=len(query) > 45,
            ),
            EvidenceItem(
                signal_name="query_frequency",
                signal_type="derived",
                value=query_frequency,
                threshold=100,
                triggered=freq_triggered,
            ),
            EvidenceItem(
                signal_name="dga_model_probability",
                signal_type="derived",
                value=round(dga_probability, 4),
                threshold=0.55,
                triggered=dga_probability > 0.55,
            ),
            EvidenceItem(
                signal_name="queried_domain",
                signal_type="raw",
                value=query,
                threshold=None,
                triggered=True,
            ),
        ]

        return self._make_result(event, confidence, evidence)
