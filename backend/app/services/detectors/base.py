from abc import ABC, abstractmethod
from typing import List
from app.schemas.detectors import DetectorInput, DetectorOutput, DetectorId

class BaseDetector(ABC):
    """
    The base interface for all future detector implementations.
    Provides the structural boundary between framework routing and detector logic.
    """

    @property
    @abstractmethod
    def detector_id(self) -> DetectorId:
        """Returns the specific detector ID this class implements."""
        pass

    @property
    @abstractmethod
    def detector_version(self) -> str:
        """Returns the version of this detector's logic."""
        pass

    @abstractmethod
    async def evaluate(self, inputs: List[DetectorInput]) -> List[DetectorOutput]:
        """
        Evaluates a set of grouped DetectorInputs and produces decisions.
        May return multiple outputs (e.g., if multiple threat types are found).
        Must handle its own missing feature logic (e.g. returning INSUFFICIENT_DATA).
        """
        pass
