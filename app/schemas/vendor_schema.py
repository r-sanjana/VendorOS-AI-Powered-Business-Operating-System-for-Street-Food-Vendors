"""
VendorOS - Vendor Schemas
Request / Response Pydantic models for the Vendor domain.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.base import VendorOSSchema


class VendorCreateRequest(VendorOSSchema):
    """Payload for POST /vendors."""

    business_name: str = Field(..., min_length=2, max_length=200)
    owner_name: str = Field(..., min_length=2, max_length=120)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = Field(None, max_length=400)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    fssai_number: Optional[str] = Field(None, max_length=50)
    gst_number: Optional[str] = Field(None, max_length=20)


class VendorUpdateRequest(VendorOSSchema):
    """Payload for PUT /vendors/{id}. All fields optional."""

    business_name: Optional[str] = Field(None, min_length=2, max_length=200)
    owner_name: Optional[str] = Field(None, min_length=2, max_length=120)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = Field(None, max_length=400)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    fssai_number: Optional[str] = Field(None, max_length=50)
    gst_number: Optional[str] = Field(None, max_length=20)


class VendorResponse(VendorOSSchema):
    """Public representation of a Vendor."""

    id: UUID
    business_name: str
    owner_name: str
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    fssai_number: Optional[str]
    gst_number: Optional[str]
    owner_id: UUID
    created_at: datetime
    updated_at: datetime