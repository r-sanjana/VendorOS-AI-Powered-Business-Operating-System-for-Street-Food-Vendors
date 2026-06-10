"""
VendorOS - Vendor Model
Represents a registered street-food vendor business.
"""

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Vendor(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    ORM model for the ``vendors`` table.

    Each Vendor is owned by exactly one User with role ``VENDOR``.
    """

    __tablename__ = "vendors"

    # ── Business identity ─────────────────────────────────────────────────────
    business_name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # ── Address ───────────────────────────────────────────────────────────────
    address: Mapped[str | None] = mapped_column(String(400), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=9, scale=6), nullable=True
    )
    longitude: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=9, scale=6), nullable=True
    )

    # ── Compliance ────────────────────────────────────────────────────────────
    fssai_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gst_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # ── FK → User ─────────────────────────────────────────────────────────────
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    owner: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="vendor"
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    inventory_items: Mapped[list["InventoryItem"]] = relationship(  # type: ignore
        "InventoryItem", back_populates="vendor", cascade="all, delete-orphan"
    )
    sales: Mapped[list["Sale"]] = relationship(  # type: ignore
        "Sale", back_populates="vendor", cascade="all, delete-orphan"
    )
    expenses: Mapped[list["Expense"]] = relationship(  # type: ignore
        "Expense", back_populates="vendor", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Vendor id={self.id} business={self.business_name}>"