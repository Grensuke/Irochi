"""
Auth business logic: authenticate, login, refresh.
"""

from __future__ import annotations

import structlog
from fastapi import HTTPException, status
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts.models import AuditLog
from app.auth.schemas import LoginRequest, RefreshRequest, TokenResponse
from app.auth.utils import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_dummy_hash,
    hash_password,
    verify_password,
)
from app.config import settings
from app.users.models import User

logger = structlog.get_logger(__name__)


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> User | None:
    """
    Validate credentials. Returns the User or None.
    Uses a dummy-hash comparison when the user is not found to prevent
    timing side-channels.
    """
    result = await db.execute(
        select(User).where(User.username == username, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()

    if user is None:
        # Timing-safe: still run the hash comparison
        verify_password(password, get_dummy_hash())
        return None

    if not verify_password(password, user.password_hash):
        return None

    # Update last_login_at
    user.last_login_at = sa_func.now()
    await db.commit()
    return user


async def login(
    db: AsyncSession,
    request: LoginRequest,
    ip_address: str | None = None,
) -> TokenResponse:
    """
    Full login flow: authenticate → issue tokens → audit log.
    """
    user = await authenticate_user(db, request.username, request.password)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token_data = {"sub": user.username, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Audit trail
    audit_entry = AuditLog(
        user_id=user.id,
        action="login",
        resource_type="session",
        ip_address=ip_address,
    )
    db.add(audit_entry)
    await db.commit()

    logger.info("user_login", username=user.username, ip=ip_address)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


async def refresh(
    db: AsyncSession, request: RefreshRequest
) -> TokenResponse:
    """
    Verify the refresh token and issue a new access token.
    The refresh token itself is NOT rotated.
    """
    payload = decode_token(request.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type: expected refresh token",
        )

    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token: missing subject",
        )

    result = await db.execute(
        select(User).where(User.username == username, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    new_access_token = create_access_token(
        {"sub": user.username, "role": user.role}
    )

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=request.refresh_token,
    )


async def create_initial_admin(db: AsyncSession) -> None:
    """
    Create the first admin user if no users exist in the database.
    Called once during app startup.
    """
    result = await db.execute(select(sa_func.count()).select_from(User))
    count = result.scalar_one()

    if count > 0:
        logger.info("initial_admin_skip", reason="users already exist")
        return

    admin = User(
        username=settings.initial_admin_username,
        email=f"{settings.initial_admin_username}@localhost",
        full_name="System Administrator",
        password_hash=hash_password(settings.initial_admin_password),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    await db.commit()

    logger.info(
        "initial_admin_created",
        username=settings.initial_admin_username,
    )
