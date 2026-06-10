"""
VendorOS - Domain Exception Hierarchy
All custom exceptions inherit from ``VendorOSException`` so they can be caught
uniformly in the global exception handler registered in ``main.py``.
"""

from typing import Any, Dict, Optional


class VendorOSException(Exception):
    """Base exception for all VendorOS domain errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        detail: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(message)


# ── 400 Bad Request ───────────────────────────────────────────────────────────

class BadRequestError(VendorOSException):
    def __init__(self, message: str = "Bad request", **kwargs: Any) -> None:
        super().__init__(message, status_code=400, **kwargs)


class DuplicateEmailError(BadRequestError):
    def __init__(self, email: str) -> None:
        super().__init__(f"Email '{email}' is already registered")


class InvalidCredentialsError(VendorOSException):
    def __init__(self) -> None:
        super().__init__("Invalid email or password", status_code=401)


class InactiveUserError(VendorOSException):
    def __init__(self) -> None:
        super().__init__("Account is deactivated", status_code=403)


# ── 404 Not Found ─────────────────────────────────────────────────────────────

class NotFoundError(VendorOSException):
    def __init__(self, resource: str, identifier: Any) -> None:
        super().__init__(f"{resource} '{identifier}' not found", status_code=404)


# ── 409 Conflict ──────────────────────────────────────────────────────────────

class ConflictError(VendorOSException):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=409)


# ── 422 Validation ────────────────────────────────────────────────────────────

class ValidationError(VendorOSException):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=422)


# ── 403 Forbidden ─────────────────────────────────────────────────────────────

class ForbiddenError(VendorOSException):
    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(message, status_code=403)