"""
Shared FastAPI dependencies: DB session, Redis, auth guards.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.utils import decode_token
from app.database import async_session_factory
from app.redis_client import get_redis_client
from app.users.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Database session ─────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session, auto-close on exit."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


# ── Redis ─────────────────────────────────────────────────────────

async def get_redis() -> aioredis.Redis:
    """Return the global Redis client singleton."""
    return get_redis_client()


# ── Auth guards ───────────────────────────────────────────────────

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Decode the JWT, load the user from the database, and verify
    that the account is still active.
    """
    payload = decode_token(token)
    username: str | None = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject",
        )

    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
        )
    return user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Raise 403 if the authenticated user is not an admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
