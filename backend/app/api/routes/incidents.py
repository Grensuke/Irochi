import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from app.schemas.incidents import IncidentResponse, IncidentListResponse, IncidentCloseRequest
from app.services.postgres_incident_service import PostgresIncidentService
from app.api.dependencies import get_postgres_incident_service

router = APIRouter()

@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    status: str | None = Query(None, description="Filter incidents by status (open, closed)"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: PostgresIncidentService = Depends(get_postgres_incident_service)
):
    incidents = await service.list_incidents(status=status, offset=offset, limit=limit)
    # Get total count (for now, simply returning 0 as we don't have a count method implemented in the service)
    # The MVP dashboard works without the exact total for incidents, but we should implement it if needed.
    return IncidentListResponse(
        incidents=[IncidentResponse.from_orm(inc) for inc in incidents],
        total=len(incidents) # simplified
    )

@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: uuid.UUID,
    service: PostgresIncidentService = Depends(get_postgres_incident_service)
):
    incident = await service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return IncidentResponse.from_orm(incident)

@router.post("/{incident_id}/close", response_model=IncidentResponse)
async def close_incident(
    incident_id: uuid.UUID,
    payload: IncidentCloseRequest,
    service: PostgresIncidentService = Depends(get_postgres_incident_service)
):
    incident = await service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if incident.status == "closed":
        raise HTTPException(status_code=400, detail="Incident is already closed")
    
    updated = await service.close_incident(
        incident_id=incident_id,
        resolution_note=payload.resolution_note,
        closed_by=payload.closed_by
    )
    return IncidentResponse.from_orm(updated)
