from abc import ABC, abstractmethod
from typing import List, Tuple
from app.schemas.detectors import DetectorInput, DetectorId
from app.schemas.features import EntityType

class GroupingInterface(ABC):
    """
    Abstract interface for multi-input grouping and temporal association.
    The exact policy (overlap join vs accumulate) and timing semantics remain OPEN.
    """

    @abstractmethod
    async def add_and_evaluate(self, detector_input: DetectorInput) -> List[DetectorInput]:
        """
        Adds a new DetectorInput to the grouping state.
        Returns the complete set of associated inputs if an evaluation is triggered,
        or an empty list if no evaluation should occur yet.
        """
        pass

    def get_base_grouping_identity(self, detector_input: DetectorInput) -> Tuple[DetectorId, EntityType, str]:
        """
        Extracts the base grouping identity from a detector input.
        """
        return (
            detector_input.detector_id,
            detector_input.feature_record.entity_type,
            detector_input.feature_record.entity_key
        )
