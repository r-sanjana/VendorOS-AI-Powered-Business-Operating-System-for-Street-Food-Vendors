"""
VendorOS - Inventory Models
InventoryItem tracks stock on hand; StockMovement records every change.
"""

import enum
import uuid
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class InventoryCategory(str, enum.Enum):
    """Predefined categories for street-food inventory."""

    RICE = "RICE"
    OIL = "OIL"
    CHICKEN = "CHICKEN"
    SPICES = "SPICES"
    VEGETABLES = "VEGETABLES"
    PACKAGING = "PACKAGING"
    BEVERAGES = "BEVERAGES"
    OTHER = "OTHER"


class MovementType(str, enum.Enum):
    """Direction of a stock movement."""

    IN = "IN"        # purchase / restock
    OUT = "OUT"      # consumption / sale
    WASTE = "WASTE"  # spoilage / write-off
    ADJUST = "ADJUST"  # manual correction


class InventoryItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A single tracked ingredient or packaging material belonging to a vendor.
    """

    __tablename__ = "inventory_items"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[InventoryCategory] = mapped_column(
        Enum(InventoryCategory, name="inventorycategory"),
        nullable=False,
        default=InventoryCategory.OTHER,
    )
    unit: Mapped[str] = mapped_column(
        String(30), nullable=False, default="kg", comment="kg, litre, piece, packet…"
    )

    # ── Stock levels ──────────────────────────────────────────────────────────
    current_stock: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, default=0
    )
    reorder_level: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, default=0,
        comment="Alert fires when current_stock ≤ reorder_level"
    )
    cost_per_unit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )

    # ── FK → Vendor ───────────────────────────────────────────────────────────
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="inventory_items")  # type: ignore

    # ── Relationships ─────────────────────────────────────────────────────────
    movements: Mapped[list["StockMovement"]] = relationship(
        "StockMovement", back_populates="item", cascade="all, delete-orphan"
    )

    @property
    def is_low_stock(self) -> bool:
        """Return True when stock is at or below the reorder level."""
        return self.current_stock <= self.reorder_level

    @property
    def inventory_value(self) -> Decimal:
        """Total value of remaining stock (current_stock × cost_per_unit)."""
        return self.current_stock * self.cost_per_unit

    def __repr__(self) -> str:
        return f"<InventoryItem id={self.id} name={self.name} stock={self.current_stock}>"


class StockMovement(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Immutable audit record of every stock change for an InventoryItem.
    """

    __tablename__ = "stock_movements"

    # ── FK → InventoryItem ────────────────────────────────────────────────────
    item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item: Mapped["InventoryItem"] = relationship("InventoryItem", back_populates="movements")

    movement_type: Mapped[MovementType] = mapped_column(
        Enum(MovementType, name="movementtype"), nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<StockMovement id={self.id} type={self.movement_type} qty={self.quantity}>"