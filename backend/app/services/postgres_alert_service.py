import uuid
from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert


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
