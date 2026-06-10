"""
VendorOS - Base Pydantic Schema
Shared config (orm_mode, json encoders) for all VendorOS schemas.
"""

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class VendorOSSchema(BaseModel):
    """
    Base schema.
    ``model_config`` enables ORM-mode so SQLAlchemy models can be passed directly.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ── Generic paginated response ─────────────────────────────────────────────────

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Wrapper for paginated list endpoints."""

    items: List[T]
    total: int
    page: int
    size: int
    pages: int

    model_config = ConfigDict(from_attributes=True)