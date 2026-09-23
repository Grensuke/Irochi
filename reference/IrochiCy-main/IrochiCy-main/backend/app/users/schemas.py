"""Users Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    id: UUID
    username: str
    full_name: Optional[str]
    email: str
    role: str
    is_active: bool
    last_login_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    full_name: Optional[str] = Field(None, max_length=128)
    email: str = Field(..., max_length=256)
    role: str = Field("analyst", pattern=r"^(admin|analyst)$")
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = Field(None, pattern=r"^(admin|analyst)$")


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=12)


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
