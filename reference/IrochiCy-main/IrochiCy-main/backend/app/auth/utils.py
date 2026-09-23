"""
Password hashing (Argon2id) and JWT token utilities.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import (
    HashingError,
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.config import settings

_ph = PasswordHasher()

# Pre-computed dummy hash for timing-safe comparison when user is not found
_DUMMY_HASH = _ph.hash("__dummy_password_for_timing_safety__")


# ── Password hashing ────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Hash a plaintext password using Argon2id with default params."""
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plaintext password against an Argon2id hash.
    Returns False on mismatch — never raises.
    """
    try:
        return _ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError, HashingError):
        return False


def get_dummy_hash() -> str:
    """Return a pre-computed dummy hash for timing-safe comparisons."""
    return _DUMMY_HASH


# ── JWT tokens ───────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a signed JWT access token.

    Payload includes: sub (username), role, type="access", exp.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(seconds=settings.access_token_expire_seconds)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(data: dict) -> str:
    """
    Create a signed JWT refresh token (7-day default expiry).

    Payload includes: sub, type="refresh", exp.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        seconds=settings.refresh_token_expire_seconds
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Raises HTTPException 401 if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )
