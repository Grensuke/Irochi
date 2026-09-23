"""Exfiltration Detector — XGBoost + byte ratio thresholds.

Processes connection events with directional byte data.
Skips events without orig_bytes/resp_bytes (per schema directional field rule).
"""

from __future__ import annotations

from typing import Optional

import structlog

from detectors.base import BaseDetector
from detectors.result import DetectorResult, EvidenceItem
from features.redis_state import RedisHotState
from features.windows import ByteRateWindow
from models.ml.exfil_model import ExfilModel

logger = structlog.get_logger(__name__)


class ExfilDetector(BaseDetector):
    """Exfiltration detector using XGBoost + byte ratio thresholds."""

    detector_id = "exfil-detector-v1"
    threat_type = "exfiltration"

    THRESHOLDS = {
        "outbound_inbound_ratio": 10.0,
        "rolling_transfer_bytes": 524_288_000,   # 500MB
        "byte_rate_orig_bps": 52_428_800,        # 50 MB/s
    }

    # High-risk destination ports
    RISK_PORTS = {4444, 6666, 1337, 8443, 9999}

    def __init__(self) -> None:
        self.model = ExfilModel()
        self.model.load()
        self.byte_window = ByteRateWindow(900)  # 15-minute window

    async def process_event(
        self,
        event,
        windows: dict,
        redis_state: RedisHotState,
    ) -> Optional[DetectorResult]:
        """Process a connection event for exfiltration indicators."""
        if event.event_type != "connection":
            return None

        # Per schema directional field rule: skip if direction unavailable
        if event.payload.orig_bytes is None or event.payload.resp_bytes is None:
            return None

        src = event.src_ip
        now = event.timestamp / 1_000_000.0

        # Update byte window
        self.byte_window.add(src, now, event.payload.orig_bytes, event.payload.resp_bytes)

        # Derive signals
        rates = self.byte_window.get_rates(src, now)
        orig_total = rates["orig_total"]
        orig_bps = rates["orig_bps"]
        ratio = rates["ratio"]

        # Duration estimate
        duration = event.payload.duration or 1.0

        # Port risk flag
        dst_port_risk = 1 if event.dst_port in self.RISK_PORTS else 0

        # Encryption flag (approximate: TLS service or port 443)
        is_encrypted = 1 if (event.payload.service == "ssl" or event.dst_port == 443) else 0

        # Build feature vector (6 features)
        features = [ratio, orig_total, orig_bps, duration, dst_port_risk, is_encrypted]

        # Run model
        model_score = self.model.predict_proba(features)

        # Check thresholds
        ratio_triggered = ratio > self.THRESHOLDS["outbound_inbound_ratio"]
        bytes_triggered = orig_total > self.THRESHOLDS["rolling_transfer_bytes"]
        bps_triggered = orig_bps > self.THRESHOLDS["byte_rate_orig_bps"]

        triggered_count = sum([ratio_triggered, bytes_triggered, bps_triggered])

        # Fire condition: at least 1 threshold triggered AND model_score > 0.35
        if triggered_count < 1 or model_score <= 0.35:
            return None

        # Confidence
        confidence = model_score * 0.70
        if ratio_triggered:
            confidence += 0.10
        if bytes_triggered:
            confidence += 0.10
        if bps_triggered:
            confidence += 0.10
        confidence = min(confidence, 1.0)

        evidence = [
            EvidenceItem(
                signal_name="outbound_inbound_ratio",
                signal_type="derived",
                value=round(ratio, 4),
                threshold=self.THRESHOLDS["outbound_inbound_ratio"],
                triggered=ratio_triggered,
            ),
            EvidenceItem(
                signal_name="rolling_transfer_bytes",
                signal_type="derived",
                value=orig_total,
                threshold=self.THRESHOLDS["rolling_transfer_bytes"],
                triggered=bytes_triggered,
            ),
            EvidenceItem(
                signal_name="byte_rate_orig_bps",
                signal_type="derived",
                value=round(orig_bps, 2),
                threshold=self.THRESHOLDS["byte_rate_orig_bps"],
                triggered=bps_triggered,
            ),
            EvidenceItem(
                signal_name="exfil_model_probability",
                signal_type="derived",
                value=round(model_score, 4),
                threshold=0.35,
                triggered=model_score > 0.35,
            ),
        ]

        return self._make_result(event, confidence, evidence)
