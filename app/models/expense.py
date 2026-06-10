"""
VendorOS - Expense Model
Tracks vendor operating expenses with category classification.
"""

import enum
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ExpenseCategory(str, enum.Enum):
    """Supported expense categories."""

    RAW_MATERIALS = "RAW_MATERIALS"
    GAS = "GAS"
    ELECTRICITY = "ELECTRICITY"
    RENT = "RENT"
    TRANSPORTATION = "TRANSPORTATION"
    SALARY = "SALARY"
    MAINTENANCE = "MAINTENANCE"
    MARKETING = "MARKETING"
    OTHER = "OTHER"


class Expense(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    ORM model for the ``expenses`` table.

    Each Expense record belongs to a single Vendor and represents money spent
    in a particular category on a given date.
    """

    __tablename__ = "expenses"

    expense_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    category: Mapped[ExpenseCategory] = mapped_column(
        Enum(ExpenseCategory, name="expensecategory"),
        nullable=False,
        default=ExpenseCategory.OTHER,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    receipt_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # ── FK → Vendor ───────────────────────────────────────────────────────────
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="expenses")  # type: ignore

    def __repr__(self) -> str:
        return (
            f"<Expense id={self.id} category={self.category} "
            f"amount={self.amount} date={self.expense_date}>"
        )