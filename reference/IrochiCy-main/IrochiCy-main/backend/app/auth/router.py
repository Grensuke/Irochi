"""Auth API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts.models import AuditLog
from app.auth import service
from app.auth.schemas import LoginRequest, RefreshRequest, TokenResponse
from app.dependencies import get_current_user, get_db
from app.users.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate and receive access + refresh tokens."""
    ip_address = request.client.host if request.client else None
    return await service.login(db, body, ip_address)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Exchange a valid refresh token for a new access token."""
    return await service.refresh(db, body)


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Log out the current user (audit trail only — JWT is stateless)."""
    ip_address = request.client.host if request.client else None
    audit_entry = AuditLog(
        user_id=current_user.id,
        action="logout",
        resource_type="session",
        ip_address=ip_address,
    )
    db.add(audit_entry)
    await db.commit()
    return {"detail": "Logged out"}
