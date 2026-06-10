"""
VendorOS - User Model
Represents platform users across all roles (ADMIN, VENDOR, EMPLOYEE, CUSTOMER).
"""

import enum
import uuid

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class UserRole(str, enum.Enum):
    """Enumeration of supported user roles."""

    ADMIN = "ADMIN"
    VENDOR = "VENDOR"
    EMPLOYEE = "EMPLOYEE"
    CUSTOMER = "CUSTOMER"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    ORM model for the ``users`` table.

    Relationships
    -------------
    vendor : ``Vendor``
        One-to-one link to the Vendor profile (VENDOR role only).
    """

    __tablename__ = "users"

    # ── Identity ──────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # ── Auth ──────────────────────────────────────────────────────────────────
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Role / Status ─────────────────────────────────────────────────────────
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole"),
        nullable=False,
        default=UserRole.CUSTOMER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    vendor: Mapped["Vendor"] = relationship(  # type: ignore[name-defined]
       "Vendor", back_populates="owner", uselist=False, lazy="select"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"