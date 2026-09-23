"""Users API routes with admin-only management and self-service endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, require_admin
from app.users import service
from app.users.models import User
from app.users.schemas import (
    PasswordChange,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


# ── Admin-only routes ────────────────────────────────────────────

@router.get("/", response_model=UserListResponse)
async def list_users(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> UserListResponse:
    """List all users (admin only)."""
    users = await service.list_users(db)
    return UserListResponse(users=users, total=len(users))


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> UserResponse:
    """Create a new user (admin only)."""
    return await service.create_user(db, body, created_by_id=admin.id)


# ── Self-service routes (must be before /{user_id}) ──────────────

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get the currently authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Update the current user's own profile (name and email only for analysts)."""
    return await service.update_user(db, current_user.id, body, current_user)


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def change_password(
    body: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change the current user's password."""
    await service.change_password(db, current_user.id, body)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Admin user management (by ID) ───────────────────────────────

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> UserResponse:
    """Get a specific user by ID (admin only)."""
    user = await service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> UserResponse:
    """Update any user (admin only)."""
    return await service.update_user(db, user_id, body, admin)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def deactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Deactivate a user (admin only, soft-delete)."""
    await service.deactivate_user(db, user_id, changed_by_id=admin.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
