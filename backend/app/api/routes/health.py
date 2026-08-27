"""Health check route."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns the health status of the backend service.",
)
def health_check() -> HealthResponse:
    """Return a simple health check response."""
    return HealthResponse(status="ok")
