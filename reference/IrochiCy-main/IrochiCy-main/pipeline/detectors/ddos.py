"""DDoS Detector — Rule-based thresholds + River streaming anomaly detection.

Processes connection events. Tracks packet rates, SYN ratios,
source IP entropy, and byte rates over 60-second rolling windows.
"""

from __future__ import annotations

import math
from typing import Optional

import structlog

from detectors.base import BaseDetector
from detectors.result import DetectorResult, EvidenceItem
from features.redis_state import RedisHotState
from features.windows import ByteRateWindow, SlidingWindowCounter, UniqueSetWindow

logger = structlog.get_logger(__name__)


class DDoSDetector(BaseDetector):
    """DDoS detector using rule-based thresholds + River anomaly scoring."""

    detector_id = "ddos-detector-v1"
    threat_type = "ddos"

    THRESHOLDS = {
        "packet_rate": 10_000,         # pkt/s from src_ip in 60s
        "byte_rate": 104_857_600,      # 100 MB/s from src_ip in 60s
        "syn_ratio": 0.85,             # SYN-only / total connections
        "source_ip_entropy": 7.0,      # Shannon entropy of unique srcs per dst
    }
    WEIGHTS = {
        "packet_rate": 0.35,
        "syn_ratio": 0.30,
        "source_ip_entropy": 0.20,
        "byte_rate": 0.15,
    }

    def __init__(self) -> None:
        self.packet_counter = SlidingWindowCounter(60)
        self.conn_counter = SlidingWindowCounter(60)
        self.syn_only_counter = SlidingWindowCounter(60)
        self.byte_tracker = ByteRateWindow(60)
        self.dst_src_sets = UniqueSetWindow(60)  # per dst_ip: set of unique src_ips
        self._river_detector = None
        self._init_river()

    def _init_river(self) -> None:
        """Initialize River HalfSpaceTrees anomaly detector."""
        try:
            from river import anomaly
            self._river_detector = anomaly.HalfSpaceTrees(
                n_trees=10, height=8, window_size=256, seed=42,
            )
        except ImportError:
            logger.warning("river_not_available_ddos_detector_rule_only")

    async def process_event(
        self,
        event,
        windows: dict,
        redis_state: RedisHotState,
    ) -> Optional[DetectorResult]:
        """Process a connection event for DDoS indicators."""
        if event.event_type != "connection":
            return None

        src = event.src_ip
        dst = event.dst_ip
        now = event.timestamp / 1_000_000.0  # µs → seconds

        # Update window trackers
        pkts = (event.payload.orig_pkts or 0) + (event.payload.resp_pkts or 0)
        self.packet_counter.add(src, now, pkts)
        self.conn_counter.add(src, now, 1)
        self.dst_src_sets.add(dst, src, now)

        # SYN-only detection via Zeek conn_state / history
        history = event.payload.history or ""
        conn_state = event.payload.conn_state or ""
        is_syn_only = conn_state in ("S0", "SH") or ("S" in history and "A" not in history)
        if is_syn_only:
            self.syn_only_counter.add(src, now, 1)

        # Byte tracking
        orig_bytes = event.payload.orig_bytes or 0
        resp_bytes = event.payload.resp_bytes or 0
        self.byte_tracker.add(src, now, orig_bytes, resp_bytes)

        # --- Derive signals ---
        total_pkts = self.packet_counter.get_count(src, now)
        packet_rate = total_pkts / 60.0

        byte_rates = self.byte_tracker.get_rates(src, now)
        byte_rate = byte_rates["orig_bps"]

        total_conns = self.conn_counter.get_count(src, now)
        syn_only_count = self.syn_only_counter.get_count(src, now)
        syn_ratio = syn_only_count / max(total_conns, 1)

        unique_src_count = self.dst_src_sets.get_unique_count(dst, now)
        source_ip_entropy = math.log2(max(unique_src_count, 1))

        # --- Score each signal 0.0-1.0 ---
        scores = {
            "packet_rate": min(packet_rate / self.THRESHOLDS["packet_rate"], 1.0),
            "syn_ratio": min(syn_ratio / self.THRESHOLDS["syn_ratio"], 1.0),
            "source_ip_entropy": min(source_ip_entropy / self.THRESHOLDS["source_ip_entropy"], 1.0),
            "byte_rate": min(byte_rate / self.THRESHOLDS["byte_rate"], 1.0),
        }

        # Weighted sum
        confidence = sum(self.WEIGHTS[s] * scores[s] for s in self.WEIGHTS)

        # River anomaly boost
        river_score = 0.0
        if self._river_detector is not None:
            x = {"packet_rate": packet_rate}
            river_score = self._river_detector.score_one(x)
            self._river_detector.learn_one(x)
            confidence += river_score * 0.15

        confidence = min(confidence, 1.0)

        # Count triggered signals
        triggered = sum(1 for s, v in scores.items() if v >= 0.5)

        # Fire condition: triggered_signals >= 2 AND confidence > 0.35
        if triggered < 2 or confidence <= 0.35:
            return None

        evidence = [
            EvidenceItem(
                signal_name="packet_rate",
                signal_type="derived",
                value=round(packet_rate, 2),
                threshold=self.THRESHOLDS["packet_rate"],
                triggered=scores["packet_rate"] >= 0.5,
            ),
            EvidenceItem(
                signal_name="syn_ratio",
                signal_type="derived",
                value=round(syn_ratio, 4),
                threshold=self.THRESHOLDS["syn_ratio"],
                triggered=scores["syn_ratio"] >= 0.5,
            ),
            EvidenceItem(
                signal_name="source_ip_entropy",
                signal_type="derived",
                value=round(source_ip_entropy, 4),
                threshold=self.THRESHOLDS["source_ip_entropy"],
                triggered=scores["source_ip_entropy"] >= 0.5,
            ),
            EvidenceItem(
                signal_name="byte_rate",
                signal_type="derived",
                value=round(byte_rate, 2),
                threshold=self.THRESHOLDS["byte_rate"],
                triggered=scores["byte_rate"] >= 0.5,
            ),
        ]

        return self._make_result(event, confidence, evidence)
