"""TLS/C2 Detector — JA3 blacklist + beacon timing analysis.

Processes TLS events. Uses SSLBL intel feed for JA3 matching
and InterArrivalTracker for beacon periodicity detection.
"""

from __future__ import annotations

import statistics
from typing import Optional

import structlog

from detectors.base import BaseDetector
from detectors.result import DetectorResult, EvidenceItem
from features.redis_state import RedisHotState
from features.windows import InterArrivalTracker
from intel.sslbl import sslbl_feed

logger = structlog.get_logger(__name__)


class TlsC2Detector(BaseDetector):
    """TLS/C2 detector using JA3 blacklist + beacon timing."""

    detector_id = "tls-c2-detector-v1"
    threat_type = "tls_c2"

    BEACON_REGULARITY_THRESHOLD = 0.90
    INTER_ARRIVAL_STD_THRESHOLD = 2.0  # seconds
    MIN_BEACON_OBSERVATIONS = 5

    def __init__(self) -> None:
        self.beacon_tracker = InterArrivalTracker(200)

    async def process_event(
        self,
        event,
        windows: dict,
        redis_state: RedisHotState,
    ) -> Optional[DetectorResult]:
        """Process a TLS event for C2 indicators."""
        if event.event_type != "tls":
            return None

        src = event.src_ip
        dst = event.dst_ip
        dst_port = event.dst_port or 0
        now = event.timestamp / 1_000_000.0

        # Beacon key: src_ip:dst_ip:dst_port
        beacon_key = f"{src}:{dst}:{dst_port}"

        # Signal 1: JA3 blacklist match
        ja3_hash = event.payload.ja3
        ja3_hit = sslbl_feed.is_malicious(ja3_hash)

        # Signal 2: Beacon timing
        self.beacon_tracker.record(beacon_key, now)
        regularity = self.beacon_tracker.get_regularity_score(beacon_key)
        intervals = self.beacon_tracker.get_intervals(beacon_key)

        beacon_triggered = False
        interval_std = None
        if regularity is not None and regularity > self.BEACON_REGULARITY_THRESHOLD:
            beacon_triggered = True

        if len(intervals) >= 2:
            interval_std = statistics.stdev(intervals)

        # Fire condition: ja3_hit OR beacon_triggered
        if not ja3_hit and not beacon_triggered:
            return None

        # Confidence
        confidence = 0.0
        if ja3_hit:
            confidence += 0.55
        if beacon_triggered and regularity is not None:
            confidence += regularity * 0.45
        confidence = min(confidence, 1.0)

        evidence = [
            EvidenceItem(
                signal_name="ja3_blacklist_match",
                signal_type="intel",
                value=ja3_hash,
                threshold=None,
                triggered=ja3_hit,
            ),
            EvidenceItem(
                signal_name="beacon_periodicity",
                signal_type="derived",
                value=round(regularity, 4) if regularity is not None else None,
                threshold=self.BEACON_REGULARITY_THRESHOLD,
                triggered=beacon_triggered,
            ),
            EvidenceItem(
                signal_name="inter_arrival_std_seconds",
                signal_type="derived",
                value=round(interval_std, 4) if interval_std is not None else None,
                threshold=self.INTER_ARRIVAL_STD_THRESHOLD,
                triggered=interval_std is not None and interval_std < self.INTER_ARRIVAL_STD_THRESHOLD,
            ),
            EvidenceItem(
                signal_name="beacon_observation_count",
                signal_type="derived",
                value=len(intervals),
                threshold=self.MIN_BEACON_OBSERVATIONS,
                triggered=len(intervals) >= self.MIN_BEACON_OBSERVATIONS,
            ),
        ]

        # Add raw signals if present
        if event.payload.server_name:
            evidence.append(EvidenceItem(
                signal_name="server_name",
                signal_type="raw",
                value=event.payload.server_name,
                threshold=None,
                triggered=False,
            ))
        if event.payload.ja4:
            evidence.append(EvidenceItem(
                signal_name="ja4",
                signal_type="raw",
                value=event.payload.ja4,
                threshold=None,
                triggered=False,
            ))

        return self._make_result(event, confidence, evidence)
