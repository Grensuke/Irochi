"""
Global exception classes for the SIH26145 backend.
"""

from __future__ import annotations


class SIHBaseException(Exception):
    """Base exception for all SIH26145 errors."""

    def __init__(self, detail: str = "An unexpected error occurred"):
        self.detail = detail
        super().__init__(self.detail)


class AuthenticationError(SIHBaseException):
    """Raised when authentication fails."""

    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(detail)


class AuthorizationError(SIHBaseException):
    """Raised when authorization fails (insufficient permissions)."""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(detail)


class ResourceNotFoundError(SIHBaseException):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str = "Resource", resource_id: str = ""):
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} '{resource_id}' not found"
        super().__init__(detail)


class DuplicateResourceError(SIHBaseException):
    """Raised when a unique constraint is violated."""

    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(detail)


class ExternalServiceError(SIHBaseException):
    """Raised when an external service (Redis, Redpanda, etc.) fails."""

    def __init__(self, service: str, detail: str = ""):
        msg = f"External service '{service}' error"
        if detail:
            msg = f"{msg}: {detail}"
        super().__init__(msg)
