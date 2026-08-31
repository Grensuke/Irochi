import uuid
import time
from typing import List, Optional, Tuple

from app.schemas.features import FeatureRecord, FeatureMechanism, EntityType, DetectorDomain
from app.schemas.detectors import (
    DetectorId, DetectorInput, DetectorOutput, Decision, SourceFeatureReference
)
from app.services.detectors.registry import DetectorRegistry
from app.services.detectors.grouping import GroupingInterface

DOMAIN_TO_DETECTOR = {
    DetectorDomain.DDOS: DetectorId.DDOS,
    DetectorDomain.RECON: DetectorId.RECON,
    DetectorDomain.DNS: DetectorId.DNS_DGA_TUNNEL,
    DetectorDomain.TLS_C2: DetectorId.TLS_C2,
    DetectorDomain.EXFIL: DetectorId.EXFILTRATION,
}

# (detector_id, mechanism, entity_type) -> bool
COMPATIBILITY_RULES = {
    (DetectorId.DDOS, FeatureMechanism.WINDOWED, EntityType.DESTINATION),

    (DetectorId.RECON, FeatureMechanism.WINDOWED, EntityType.SOURCE),

    (DetectorId.DNS_DGA_TUNNEL, FeatureMechanism.ENRICHMENT, EntityType.SOURCE),
    (DetectorId.DNS_DGA_TUNNEL, FeatureMechanism.WINDOWED, EntityType.SOURCE),

    (DetectorId.TLS_C2, FeatureMechanism.ENRICHMENT, EntityType.CONNECTION),
    (DetectorId.TLS_C2, FeatureMechanism.CORRELATION, EntityType.CONNECTION),
    (DetectorId.TLS_C2, FeatureMechanism.WINDOWED, EntityType.PAIR),

    (DetectorId.EXFILTRATION, FeatureMechanism.WINDOWED, EntityType.SOURCE),
}

class DetectorRouter:
    """
    Routes FeatureRecords to appropriate detectors, validating compatibility,
    handling grouping, and managing the framework boundary.
    """
    def __init__(self, registry: DetectorRegistry, grouping: GroupingInterface):
        self.registry = registry
        self.grouping = grouping
        self.router_version = "1.0.0"

    def _create_error_output(
        self,
        record: FeatureRecord,
        detector_id: DetectorId,
        decision: Decision,
        evidence: dict
    ) -> DetectorOutput:
        return DetectorOutput(
            output_id=str(uuid.uuid4()),
            detector_id=detector_id,
            input_id=str(uuid.uuid4()), # Dummy input ID since it failed before creation
            entity_type=record.entity_type,
            entity_key=record.entity_key,
            evaluated_at=int(time.time() * 1000000),
            detector_version=self.router_version,
            decision=decision,
            evidence=evidence,
            source_feature_references=[
                SourceFeatureReference(feature_id=record.feature_id, revision=record.revision)
            ]
        )

    def _validate_record(self, record: FeatureRecord, detector_id: DetectorId) -> Optional[str]:
        # Mechanism/Entity compatibility
        rule_key = (detector_id, record.mechanism, record.entity_type)
        if rule_key not in COMPATIBILITY_RULES:
            return f"Incompatible combination: {detector_id.value}, {record.mechanism.value}, {record.entity_type.value}"

        # Window metadata presence/absence
        if record.mechanism == FeatureMechanism.ENRICHMENT:
            if record.window_type is not None or record.window_start is not None or record.window_end is not None:
                return "Enrichment records must not have temporal window fields"
        elif record.mechanism == FeatureMechanism.WINDOWED:
            if record.window_type is None or record.window_start is None or record.window_end is None:
                return "Windowed records must have window_type, window_start, and window_end"

        return None

    async def route(self, record: FeatureRecord) -> List[DetectorOutput]:
        """
        Main entry point for the framework boundary.
        Validates the record, groups it if necessary, and dispatches to the detector.
        """
        detector_id = DOMAIN_TO_DETECTOR.get(record.detector_domain)
        if not detector_id:
            raise ValueError(f"Unsupported detector domain: {record.detector_domain}")

        validation_error = self._validate_record(record, detector_id)
        if validation_error:
            return [self._create_error_output(
                record, detector_id, Decision.INVALID_INPUT, {"reason": validation_error}
            )]

        # Valid input, construct DetectorInput
        detector_input = DetectorInput(
            input_id=str(uuid.uuid4()),
            detector_id=detector_id,
            feature_record=record
        )

        # Retrieve registered detector
        detector = self.registry.get_detector(detector_id)
        if not detector:
            return [self._create_error_output(
                record, detector_id, Decision.DETECTOR_ERROR, {"reason": f"Detector not registered: {detector_id.value}"}
            )]

        # Pass to grouping interface
        inputs_to_evaluate = await self.grouping.add_and_evaluate(detector_input)

        if not inputs_to_evaluate:
            # Grouping interface decided not to evaluate yet (e.g. accumulating)
            return []

        # Dispatch
        try:
            outputs = await detector.evaluate(inputs_to_evaluate)
            return outputs
        except Exception as e:
            return [self._create_error_output(
                record, detector_id, Decision.DETECTOR_ERROR, {"reason": f"Detector evaluation exception: {str(e)}"}
            )]
