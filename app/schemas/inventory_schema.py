"""
VendorOS - Inventory Schemas
Request / Response Pydantic models for Inventory and StockMovement.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.models.inventory import InventoryCategory, MovementType
from app.schemas.base import VendorOSSchema


# ── InventoryItem ─────────────────────────────────────────────────────────────

class InventoryItemCreateRequest(VendorOSSchema):
    name: str = Field(..., min_length=1, max_length=150)
    category: InventoryCategory = InventoryCategory.OTHER
    unit: str = Field(default="kg", max_length=30)
    current_stock: Decimal = Field(default=Decimal("0"), ge=0)
    reorder_level: Decimal = Field(default=Decimal("0"), ge=0)
    cost_per_unit: Decimal = Field(default=Decimal("0"), ge=0)
    vendor_id: UUID


class InventoryItemUpdateRequest(VendorOSSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    category: Optional[InventoryCategory] = None
    unit: Optional[str] = Field(None, max_length=30)
    current_stock: Optional[Decimal] = Field(None, ge=0)
    reorder_level: Optional[Decimal] = Field(None, ge=0)
    cost_per_unit: Optional[Decimal] = Field(None, ge=0)


class InventoryItemResponse(VendorOSSchema):
    id: UUID
    name: str
    category: InventoryCategory
    unit: str
    current_stock: Decimal
    reorder_level: Decimal
    cost_per_unit: Decimal
    is_low_stock: bool
    inventory_value: Decimal
    vendor_id: UUID
    created_at: datetime
    updated_at: datetime


# ── StockMovement ─────────────────────────────────────────────────────────────

class StockMovementCreateRequest(VendorOSSchema):
    """Record a stock IN/OUT/WASTE/ADJUST movement."""

    item_id: UUID
    movement_type: MovementType
    quantity: Decimal = Field(..., gt=0)
    notes: Optional[str] = Field(None, max_length=500)


class StockMovementResponse(VendorOSSchema):
    id: UUID
    item_id: UUID
    movement_type: MovementType
    quantity: Decimal
    notes: Optional[str]
    created_at: datetime


# ── Low-stock alert ───────────────────────────────────────────────────────────

class LowStockAlert(VendorOSSchema):
    """Summary object returned in low-stock alerts."""

    item_id: UUID
    item_name: str
    current_stock: Decimal
    reorder_level: Decimal
    unit: str
    category: InventoryCategory