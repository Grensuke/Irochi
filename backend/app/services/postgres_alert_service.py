import uuid
from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.schemas.dashboard import DashboardSummaryResponse
from app.schemas.alerts import AlertResponse


class StaleUpdateError(Exception):
    """Raised when an update fails due to a mismatched expected_update_count."""
    pass


class PostgresAlertService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_alert(self, alert: Alert) -> Alert:
        """Create a new alert in PostgreSQL."""
        self.session.add(alert)
        await self.session.commit()
        await self.session.refresh(alert)
        return alert

    async def get_alert(self, alert_id: uuid.UUID) -> Alert | None:
        """Fetch a single alert by ID."""
        stmt = select(Alert).where(Alert.alert_id == alert_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_open_alert_by_identity(
        self,
        detector_id: str,
        threat_type: str,
        entity_type: str,
        entity_key: str
    ) -> Alert | None:
        """Find an existing 'new' alert matching the deduplication identity."""
        stmt = select(Alert).where(
            Alert.detector_id == detector_id,
            Alert.threat_type == threat_type,
            Alert.entity_type == entity_type,
            Alert.entity_key == entity_key,
            Alert.status == "new"
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_alerts(
        self,
        offset: int | None = None,
        limit: int | None = None,
    ) -> Sequence[Alert]:
        """
        Provides generic persistence query specification.
        The API layer remains responsible for API-specific defaults,
        query parameter validation, final API filtering semantics, and pagination limits.
        """
        stmt = select(Alert).order_by(Alert.detected_at.desc())
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_dashboard_summary(self) -> DashboardSummaryResponse:
        """Compute dashboard metrics directly via SQL aggregation."""
        severity_stmt = select(Alert.severity, func.count(Alert.alert_id)).group_by(Alert.severity)
        severity_rows = (await self.session.execute(severity_stmt)).all()
        severity_counts = {sev: count for sev, count in severity_rows}

        threat_stmt = select(Alert.threat_type, func.count(Alert.alert_id)).group_by(Alert.threat_type)
        threat_rows = (await self.session.execute(threat_stmt)).all()
        by_threat_type = {threat: count for threat, count in threat_rows}

        detector_stmt = select(Alert.detector_id, func.count(Alert.alert_id)).group_by(Alert.detector_id)
        detector_rows = (await self.session.execute(detector_stmt)).all()
        by_detector = {det: count for det, count in detector_rows}

        recent_stmt = select(Alert).order_by(Alert.last_seen_at.desc()).limit(5)
        recent_orm = (await self.session.execute(recent_stmt)).scalars().all()

        recent_alerts = []
        for a in recent_orm:
            recent_alerts.append(AlertResponse(
                alert_id=str(a.alert_id),
                timestamp=a.last_seen_at,
                threat_type=a.threat_type,
                detector_id=a.detector_id,
                severity=a.severity,
                confidence=a.confidence or 0.0,
                entity_type=a.entity_type,
                entity_key=a.entity_key,
                first_seen_at=a.first_seen_at,
                last_seen_at=a.last_seen_at,
                resolved_at=a.resolved_at,
                evidence_summary=a.evidence_summary or "",
                status=a.status
            ))

        total_alerts = sum(severity_counts.values())

        return DashboardSummaryResponse(
            total_alerts=total_alerts,
            critical_count=severity_counts.get("critical", 0),
            high_count=severity_counts.get("high", 0),
            medium_count=severity_counts.get("medium", 0),
            low_count=severity_counts.get("low", 0),
            info_count=severity_counts.get("info", 0),
            by_threat_type=by_threat_type,
            by_detector=by_detector,
            recent_alerts=recent_alerts,
        )

    async def update_alert_fields(
        self,
        alert_id: uuid.UUID,
        updates: dict[str, Any],
        expected_update_count: int,
    ) -> Alert:
        """
        Implementation primitive capable of supporting safe concurrent updates.
        This is NOT the final approved concurrency algorithm, which remains OPEN for WP-H.
        """
        updates["update_count"] = expected_update_count + 1

        stmt = (
            update(Alert)
            .where(
                Alert.alert_id == alert_id,
                Alert.update_count == expected_update_count
            )
            .values(**updates)
            .returning(Alert)
        )

        result = await self.session.execute(stmt)
        updated_alert = result.scalar_one_or_none()

        if updated_alert is None:
            # Differentiate between non-existent alert and stale update
            exists_stmt = select(Alert.alert_id).where(Alert.alert_id == alert_id)
            exists_result = await self.session.execute(exists_stmt)
            if exists_result.scalar_one_or_none() is not None:
                raise StaleUpdateError(f"Stale update for alert {alert_id} (expected count {expected_update_count})")
            raise ValueError(f"Alert {alert_id} not found")

        await self.session.commit()
        return updated_alert
