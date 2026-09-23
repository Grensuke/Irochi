"""Recon Detector — Statistical window-based thresholds for port/host scanning.

Processes connection events. Tracks unique destination ports, unique hosts,
scan rate, and connection fan-out over 60-second rolling windows.
"""

from __future__ import annotations

from typing import Optional

import structlog

from detectors.base import BaseDetector
from detectors.result import DetectorResult, EvidenceItem
from features.redis_state import RedisHotState
from features.windows import SlidingWindowCounter, UniqueSetWindow

logger = structlog.get_logger(__name__)


class ReconDetector(BaseDetector):
    """Reconnaissance/scanning detector using statistical thresholds."""

    detector_id = "recon-detector-v1"
    threat_type = "recon"

    THRESHOLDS = {
        "unique_dst_ports": 1000,      # unique ports per src in 60s
        "unique_dst_hosts": 500,       # unique hosts per src in 60s
        "scan_rate": 50,               # connections/sec from src
        "connection_fan_out": 0.8,     # unique_dst_hosts / total_connections
    }
    WEIGHTS = {
        "unique_dst_ports": 0.40,
        "unique_dst_hosts": 0.30,
        "scan_rate": 0.20,
        "connection_fan_out": 0.10,
    }

    def __init__(self) -> None:
        self.dst_ports = UniqueSetWindow(60)    # per src: unique dst ports
        self.dst_hosts = UniqueSetWindow(60)    # per src: unique dst hosts
        self.conn_count = SlidingWindowCounter(60)

    async def process_event(
        self,
        event,
        windows: dict,
        redis_state: RedisHotState,
    ) -> Optional[DetectorResult]:
        """Process a connection event for reconnaissance indicators."""
        if event.event_type != "connection":
            return None

        src = event.src_ip
        now = event.timestamp / 1_000_000.0

        # Update trackers
        if event.dst_port is not None:
            self.dst_ports.add(src, str(event.dst_port), now)
        self.dst_hosts.add(src, event.dst_ip, now)
        self.conn_count.add(src, now, 1)

        # Derive signals
        unique_ports = self.dst_ports.get_unique_count(src, now)
        unique_hosts = self.dst_hosts.get_unique_count(src, now)
        total_conns = self.conn_count.get_count(src, now)
        scan_rate = total_conns / 60.0
        fan_out = unique_hosts / max(total_conns, 1)

        # Score each signal 0.0-1.0
        scores = {
            "unique_dst_ports": min(unique_ports / self.THRESHOLDS["unique_dst_ports"], 1.0),
            "unique_dst_hosts": min(unique_hosts / self.THRESHOLDS["unique_dst_hosts"], 1.0),
            "scan_rate": min(scan_rate / self.THRESHOLDS["scan_rate"], 1.0),
            "connection_fan_out": min(fan_out / self.THRESHOLDS["connection_fan_out"], 1.0),
        }

        # Weighted sum
        confidence = sum(self.WEIGHTS[s] * scores[s] for s in self.WEIGHTS)
        confidence = min(confidence, 1.0)

        # Count triggered
        triggered = sum(1 for v in scores.values() if v >= 0.5)

        # Fire condition: at least 1 triggered AND confidence > 0.25
        if triggered < 1 or confidence <= 0.25:
            return None

        evidence = [
            EvidenceItem(
                signal_name="unique_dst_ports",
                signal_type="derived",
                value=unique_ports,
                threshold=self.THRESHOLDS["unique_dst_ports"],
                triggered=scores["unique_dst_ports"] >= 0.5,
            ),
            EvidenceItem(
                signal_name="unique_dst_hosts",
                signal_type="derived",
                value=unique_hosts,
                threshold=self.THRESHOLDS["unique_dst_hosts"],
                triggered=scores["unique_dst_hosts"] >= 0.5,
            ),
            EvidenceItem(
                signal_name="scan_rate",
                signal_type="derived",
                value=round(scan_rate, 2),
                threshold=self.THRESHOLDS["scan_rate"],
                triggered=scores["scan_rate"] >= 0.5,
            ),
            EvidenceItem(
                signal_name="connection_fan_out",
                signal_type="derived",
                value=round(fan_out, 4),
                threshold=self.THRESHOLDS["connection_fan_out"],
                triggered=scores["connection_fan_out"] >= 0.5,
            ),
        ]

        return self._make_result(event, confidence, evidence)
