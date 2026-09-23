"""BaseDetector — Abstract base class for all threat detectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from detectors.result import DetectorResult, EvidenceItem
from features.redis_state import RedisHotState


class BaseDetector(ABC):
    """Abstract base class for all threat detectors.

    Subclasses must override:
      - detector_id (str)
      - threat_type (str)
      - process_event()
    """

    detector_id: str = "base-detector"
    threat_type: str = "unknown"

    @abstractmethod
    async def process_event(
        self,
        event,
        windows: dict,
        redis_state: RedisHotState,
    ) -> Optional[DetectorResult]:
        """Process a canonical event and optionally return a detection result."""
        ...

    def _make_result(
        self,
        event,
        confidence: float,
        evidence: list[EvidenceItem],
    ) -> DetectorResult:
        """Convenience builder for DetectorResult from event fields."""
        return DetectorResult(
            event_id=event.event_id,
            threat_type=self.threat_type,
            detector_id=self.detector_id,
            confidence=min(confidence, 1.0),
            evidence=evidence,
            src_ip=event.src_ip,
            dst_ip=event.dst_ip,
            src_port=event.src_port,
            dst_port=event.dst_port,
            protocol=event.protocol,
            sensor_source=event.sensor_source,
        )
