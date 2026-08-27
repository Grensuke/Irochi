"""Health check schemas."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response model for the health endpoint."""

    status: str = "ok"
