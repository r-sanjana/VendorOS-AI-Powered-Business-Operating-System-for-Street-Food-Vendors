"""
VendorOS - Sales Models
Sale is the transaction header; SaleItem is each line item within a sale.
"""

import enum
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class PaymentMethod(str, enum.Enum):
    """Accepted payment methods."""

    CASH = "CASH"
    UPI = "UPI"
    CARD = "CARD"


class Sale(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Represents a single sales transaction.

    ``total_amount`` is the authoritative total; it can be computed from
    ``SaleItem`` rows or supplied directly (e.g. for partial records).
    """

    __tablename__ = "sales"

    sale_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="paymentmethod"),
        nullable=False,
        default=PaymentMethod.CASH,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── FK → Vendor ───────────────────────────────────────────────────────────
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="sales")  # type: ignore

    # ── Relationships ─────────────────────────────────────────────────────────
    items: Mapped[list["SaleItem"]] = relationship(
        "SaleItem", back_populates="sale", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Sale id={self.id} date={self.sale_date} total={self.total_amount}>"


class SaleItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A single line item within a ``Sale`` (product, quantity, unit price).
    """

    __tablename__ = "sale_items"

    sale_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sale: Mapped["Sale"] = relationship("Sale", back_populates="items")

    item_name: Mapped[str] = mapped_column(String(150), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    @property
    def line_total(self) -> Decimal:
        """Return quantity × unit_price."""
        return Decimal(self.quantity) * self.unit_price

    def __repr__(self) -> str:
        return (
            f"<SaleItem id={self.id} item={self.item_name} "
            f"qty={self.quantity} price={self.unit_price}>"
        )