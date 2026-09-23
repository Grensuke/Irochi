"""Users business logic with audit logging and privilege enforcement."""

from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts.models import AuditLog
from app.auth.utils import hash_password, verify_password
from app.users.models import User
from app.users.schemas import PasswordChange, UserCreate, UserResponse, UserUpdate

logger = structlog.get_logger(__name__)


async def list_users(db: AsyncSession) -> list[UserResponse]:
    """List all users ordered by creation date."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return [UserResponse.model_validate(u) for u in result.scalars().all()]


async def get_user(db: AsyncSession, user_id: UUID) -> UserResponse | None:
    """Get a single user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        return None
    return UserResponse.model_validate(user)


async def get_user_model(db: AsyncSession, user_id: UUID) -> User | None:
    """Get raw User ORM model by ID (for internal use)."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    data: UserCreate,
    created_by_id: UUID,
) -> UserResponse:
    """Create a new user account with audit logging."""

    # Check username uniqueness
    existing_username = await db.execute(
        select(User).where(User.username == data.username)
    )
    if existing_username.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{data.username}' already exists",
        )

    # Check email uniqueness
    existing_email = await db.execute(
        select(User).where(User.email == data.email)
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{data.email}' already exists",
        )

    user = User(
        username=data.username,
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(user)

    audit = AuditLog(
        user_id=created_by_id,
        action="user_created",
        resource_type="user",
        payload={"created_username": data.username, "role": data.role},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(user)
    logger.info("user_created", username=user.username, by=str(created_by_id))
    return UserResponse.model_validate(user)


async def update_user(
    db: AsyncSession,
    user_id: UUID,
    data: UserUpdate,
    current_user: User,
) -> UserResponse:
    """
    Update user fields with privilege enforcement.
    Analysts can only update their own full_name and email.
    Admins can update any field on any user.
    Cannot demote own role.
    """
    target = await get_user_model(db, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")

    is_self = current_user.id == user_id
    is_admin = current_user.role == "admin"

    # Analyst can only edit themselves, and only name/email
    if not is_admin:
        if not is_self:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Analysts can only update their own profile",
            )
        if data.role is not None or data.is_active is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Analysts cannot change role or active status",
            )

    # Admin cannot demote their own role
    if is_admin and is_self and data.role is not None and data.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote your own admin role",
        )

    if data.full_name is not None:
        target.full_name = data.full_name
    if data.email is not None:
        target.email = data.email
    if data.role is not None:
        target.role = data.role
    if data.is_active is not None:
        target.is_active = data.is_active

    await db.commit()
    await db.refresh(target)
    logger.info("user_updated", user_id=str(user_id), by=str(current_user.id))
    return UserResponse.model_validate(target)


async def change_password(
    db: AsyncSession,
    user_id: UUID,
    req: PasswordChange,
) -> None:
    """Change a user's password after verifying the current one."""
    user = await get_user_model(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(req.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    user.password_hash = hash_password(req.new_password)

    audit = AuditLog(
        user_id=user_id,
        action="password_changed",
        resource_type="user",
        resource_id=user_id,
    )
    db.add(audit)

    await db.commit()
    logger.info("password_changed", user_id=str(user_id))


async def deactivate_user(
    db: AsyncSession,
    user_id: UUID,
    changed_by_id: UUID,
) -> None:
    """Soft-delete a user (set is_active=False) with safety checks."""
    if user_id == changed_by_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself",
        )

    target = await get_user_model(db, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent removing the last admin
    if target.role == "admin":
        admin_count = await db.execute(
            select(func.count())
            .select_from(User)
            .where(User.role == "admin", User.is_active.is_(True))
        )
        if admin_count.scalar_one() <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate the last active admin",
            )

    target.is_active = False

    audit = AuditLog(
        user_id=changed_by_id,
        action="user_deactivated",
        resource_type="user",
        resource_id=user_id,
        payload={"deactivated_username": target.username},
    )
    db.add(audit)

    await db.commit()
    logger.info("user_deactivated", user_id=str(user_id), by=str(changed_by_id))
