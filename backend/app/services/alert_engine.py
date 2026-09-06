import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.schemas.detectors import DetectorOutput, Decision
from app.schemas.alerts import AlertStatus, Severity
from app.services.postgres_alert_service import PostgresAlertService
from app.services.redis_pubsub import RedisPubSubService
from app.models.alert import Alert

logger = logging.getLogger(__name__)

class AlertEngine:
    def __init__(
        self,
        postgres_service: PostgresAlertService,
        redis_service: RedisPubSubService
    ):
        self.postgres_service = postgres_service
        self.redis_service = redis_service

    async def process_detector_output(self, output: DetectorOutput) -> Optional[dict]:
        """
        Processes a generic DetectorOutput event.
        - Drops NO_THREAT / INSUFFICIENT_DATA.
        - Logs and drops INVALID_INPUT / DETECTOR_ERROR.
        - Persists DETECTION to Postgres.
        - Dedupes matching open alerts by (detector_id, threat_type, entity_type, entity_key).
        - Publishes to Redis after commit.
        """
        # 1. Decision Filtering
        logger.info(f"AlertEngine received output from {output.detector_id} with decision {output.decision}")
        if output.decision in (Decision.NO_THREAT, Decision.INSUFFICIENT_DATA):
            return None

        if output.decision in (Decision.INVALID_INPUT, Decision.DETECTOR_ERROR):
            logger.error(
                "Operational error in detector_output",
                extra={
                    "detector_id": output.detector_id,
                    "decision": output.decision.value,
                    "evidence": output.evidence
                }
            )
            return None

        if output.decision != Decision.DETECTION:
            logger.warning(f"Unknown decision type: {output.decision}")
            return None

        # 2. Extract Identity
        # Use entity_type and entity_key natively from payload if present
        # Fallback to defaults to guarantee 4-tuple presence, though the schema ensures they exist
        entity_type = output.entity_type
        entity_key = output.entity_key

        # 3. Handle Severity Fallback
        severity = output.severity_candidate if output.severity_candidate else Severity.MEDIUM.value

        # Prepare evidence
        evidence = output.evidence or {}

        # 4. Deduplication
        existing_alert = await self.postgres_service.get_open_alert_by_identity(
            detector_id=output.detector_id,
            threat_type=output.threat_type,
            entity_type=entity_type,
            entity_key=entity_key
        )

        if output.evaluated_at:
            detected_at = datetime.fromtimestamp(output.evaluated_at / 1_000_000, tz=timezone.utc)
        else:
            detected_at = datetime.now(timezone.utc)

        current_time = datetime.now(timezone.utc)

        # Evidence payload
        # Ensure evidence is a dict. The summary should be a string representation.
        if isinstance(evidence, dict):
            evidence_summary = str(evidence.get("message", "Detected anomalous behavior")) if evidence else "Detected anomalous behavior"
        else:
            evidence_summary = str(evidence)
            evidence = {"raw": evidence}

        # Validate severity candidate exists, else fallback
        severity_val = output.severity_candidate.value if output.severity_candidate else Severity.MEDIUM.value

        # source_feature_references must be a list of dicts for JSONB
        sf_refs = [
            r.model_dump(mode="json") if hasattr(r, "model_dump") else (r.dict() if hasattr(r, "dict") else r)
            for r in output.source_feature_references
        ]

        if existing_alert:
            # Update existing alert
            # We use optimistic concurrency on update_count natively in postgres_alert_service
            # We merge evidence and update timestamp
            new_evidence = dict(existing_alert.evidence) if existing_alert.evidence else {}
            new_evidence.update(evidence)

            updates = {
                "detector_output_id": output.output_id,
                "detector_version": output.detector_version,
                "model_version": output.model_version,
                "source_feature_references": sf_refs,
                "score": output.score,
                "severity_candidate": severity_val,
                "last_seen_at": detected_at,
                "confidence": output.confidence,
                "evidence": new_evidence,
                "evidence_summary": evidence_summary,
                "severity": severity_val, # Assume severity might get updated
            }

            try:
                updated_alert = await self.postgres_service.update_alert_fields(
                    alert_id=existing_alert.alert_id,
                    updates=updates,
                    expected_update_count=existing_alert.update_count
                )
                alert_to_publish = updated_alert
            except Exception as e:
                logger.error(f"Failed to update alert {existing_alert.alert_id} - concurrency issue or not found: {e}")
                return None

        else:
            # Create new alert
            # Note: MVP Limitation - No database-level unique constraint on the 4-tuple for concurrent inserts
            new_alert = Alert(
                alert_id=uuid.uuid4(),
                detector_output_id=output.output_id,
                detector_id=output.detector_id.value if hasattr(output.detector_id, "value") else output.detector_id,
                threat_type=output.threat_type.value if hasattr(output.threat_type, "value") else output.threat_type,
                entity_type=entity_type.value if hasattr(entity_type, "value") else entity_type,
                entity_key=entity_key,
                detected_at=detected_at,
                created_at=current_time,
                first_seen_at=current_time,
                last_seen_at=detected_at,
                status=AlertStatus.NEW.value,
                severity=severity_val,
                severity_candidate=severity_val,
                confidence=output.confidence,
                score=output.score,
                title=f"{output.threat_type} detected for {entity_type} {entity_key}",
                evidence_summary=evidence_summary,
                evidence=evidence,
                source_feature_references=sf_refs,
                detector_version=output.detector_version,
                model_version=output.model_version,
                schema_version=output.schema_version,
                update_count=0,
                resolved_at=None
            )

            try:
                alert_to_publish = await self.postgres_service.create_alert(new_alert)
            except Exception as e:
                logger.exception("Failed to commit alert to PostgreSQL")
                return None

        # 6. Redis Publish
        # Create dictionary payload for pubsub
        # We manually map the ORM attributes since it's an SQLAlchemy model
        alert_payload = {
            "alert_id": str(alert_to_publish.alert_id),
            "timestamp": alert_to_publish.last_seen_at.isoformat(),
            "first_seen_at": alert_to_publish.first_seen_at.isoformat() if alert_to_publish.first_seen_at else alert_to_publish.last_seen_at.isoformat(),
            "last_seen_at": alert_to_publish.last_seen_at.isoformat(),
            "threat_type": alert_to_publish.threat_type,
            "detector_id": alert_to_publish.detector_id,
            "severity": alert_to_publish.severity,
            "confidence": alert_to_publish.confidence,
            "evidence_summary": alert_to_publish.evidence_summary,
            "status": alert_to_publish.status,
            "entity_type": alert_to_publish.entity_type,
            "entity_key": alert_to_publish.entity_key
        }

        try:
            await self.redis_service.publish_alert(alert_payload)
        except Exception as e:
            # If Redis fails, the alert remains successfully committed in DB
            # We log the failure but do not rollback DB
            logger.exception(f"Failed to publish alert {alert_to_publish.alert_id} to Redis")

        return alert_payload
