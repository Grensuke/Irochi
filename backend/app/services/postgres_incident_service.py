import uuid
from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident


class PostgresIncidentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_incident(self, incident: Incident) -> Incident:
        """Create a new incident in PostgreSQL."""
        self.session.add(incident)
        await self.session.commit()
        await self.session.refresh(incident)
        return incident

    async def get_incident(self, incident_id: uuid.UUID) -> Incident | None:
        """Fetch a single incident by ID."""
        stmt = select(Incident).where(Incident.incident_id == incident_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_open_incident_for_src_ip(
        self,
        src_ip: str,
        window_start: datetime
    ) -> Incident | None:
        """
        Find an open incident for the given source IP where the last event
        occurred after the window_start.
        entity_type is assumed to be 'source'.
        """
        stmt = select(Incident).where(
            Incident.entity_type == "source",
            Incident.entity_key == src_ip,
            Incident.status == "open",
            Incident.last_event_at >= window_start
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_incidents(
        self,
        status: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> Sequence[Incident]:
        """
        List incidents, optionally filtered by status, ordered by risk_score DESC.
        """
        stmt = select(Incident).order_by(Incident.risk_score.desc())
        
        if status is not None:
            stmt = stmt.where(Incident.status == status)
            
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
            
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_incident_fields(
        self,
        incident_id: uuid.UUID,
        updates: dict[str, Any],
    ) -> Incident:
        """
        Update fields on an existing incident.
        No optimistic locking is implemented yet as concurrent updates
        for the same entity are not expected in this architecture.
        """
        stmt = (
            update(Incident)
            .where(Incident.incident_id == incident_id)
            .values(**updates)
            .returning(Incident)
        )

        result = await self.session.execute(stmt)
        updated_incident = result.scalar_one_or_none()

        if updated_incident is None:
            raise ValueError(f"Incident {incident_id} not found")

        await self.session.commit()
        return updated_incident
