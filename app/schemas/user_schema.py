"""
VendorOS - User Schemas
Request / Response Pydantic models for the User domain.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.models.user import UserRole
from app.schemas.base import VendorOSSchema


# ── Request schemas ────────────────────────────────────────────────────────────

class UserRegisterRequest(VendorOSSchema):
    """Payload for POST /auth/register."""

    name: str = Field(..., min_length=2, max_length=120, examples=["Ravi Kumar"])
    email: EmailStr = Field(..., examples=["ravi@example.com"])
    phone: Optional[str] = Field(None, max_length=20, examples=["+919876543210"])
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = Field(default=UserRole.CUSTOMER)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Require at least one digit and one letter."""
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        return v


class UserLoginRequest(VendorOSSchema):
    """Payload for POST /auth/login."""

    email: EmailStr = Field(..., examples=["ravi@example.com"])
    password: str = Field(..., min_length=1)


# ── Response schemas ───────────────────────────────────────────────────────────

class UserResponse(VendorOSSchema):
    """Safe public representation of a User (no password hash)."""

    id: UUID
    name: str
    email: str
    phone: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TokenResponse(VendorOSSchema):
    """JWT tokens returned after successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class AuthResponse(VendorOSSchema):
    """Combined auth response with user data and tokens."""

    user: UserResponse
    tokens: TokenResponse


# ── Update schemas ─────────────────────────────────────────────────────────────

class UserUpdateRequest(VendorOSSchema):
    """Payload for PATCH /users/{id}."""

    name: Optional[str] = Field(None, min_length=2, max_length=120)
    phone: Optional[str] = Field(None, max_length=20)