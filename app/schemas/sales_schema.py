"""
VendorOS - Sales Schemas
Request / Response Pydantic models for Sale and SaleItem.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field, model_validator

from app.models.sales import PaymentMethod
from app.schemas.base import VendorOSSchema


# ── SaleItem ───────────────────────────────────────────────────────────────────

class SaleItemCreateRequest(VendorOSSchema):
    item_name: str = Field(..., min_length=1, max_length=150)
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)


class SaleItemResponse(VendorOSSchema):
    id: UUID
    item_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


# ── Sale ───────────────────────────────────────────────────────────────────────

class SaleCreateRequest(VendorOSSchema):
    vendor_id: UUID
    sale_date: date
    payment_method: PaymentMethod = PaymentMethod.CASH
    items: List[SaleItemCreateRequest] = Field(..., min_length=1)
    notes: Optional[str] = Field(None, max_length=500)


class SaleResponse(VendorOSSchema):
    id: UUID
    vendor_id: UUID
    sale_date: date
    payment_method: PaymentMethod
    total_amount: Decimal
    notes: Optional[str]
    items: List[SaleItemResponse]
    created_at: datetime
    updated_at: datetime


# ── Revenue summaries ─────────────────────────────────────────────────────────

class RevenueSummary(VendorOSSchema):
    """Aggregated revenue for a period."""

    period: str        # e.g. "2024-05-01" / "2024-W18" / "2024-05"
    total_revenue: Decimal
    transaction_count: int


class TopProduct(VendorOSSchema):
    """Best-selling product entry."""

    item_name: str
    total_quantity: int
    total_revenue: Decimal