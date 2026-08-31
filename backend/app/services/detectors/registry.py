from typing import Dict, Optional
from app.schemas.detectors import DetectorId
from app.services.detectors.base import BaseDetector

class DetectorRegistry:
    """
    Holds registered detector implementations.
    Does not contain detector algorithms or framework routing logic.
    """
    def __init__(self):
        self._detectors: Dict[DetectorId, BaseDetector] = {}

    def register(self, detector: BaseDetector):
        """Registers a detector instance."""
        if detector.detector_id in self._detectors:
            raise ValueError(f"Detector {detector.detector_id.value} is already registered.")
        self._detectors[detector.detector_id] = detector

    def get_detector(self, detector_id: DetectorId) -> Optional[BaseDetector]:
        """Retrieves a registered detector by ID."""
        return self._detectors.get(detector_id)

    def is_registered(self, detector_id: DetectorId) -> bool:
        """Checks if a detector is registered."""
        return detector_id in self._detectors
