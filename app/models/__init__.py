"""
Import all ORM models here so Alembic's ``env.py`` only needs to import
this module to discover all metadata.
"""

from app.models.user import User, UserRole
from app.models.vendor import Vendor
from app.models.inventory import InventoryItem, StockMovement, InventoryCategory, MovementType
from app.models.sales import Sale, SaleItem, PaymentMethod
from app.models.expense import Expense, ExpenseCategory

__all__ = [
    "User",
    "UserRole",
    "Vendor",
    "InventoryItem",
    "StockMovement",
    "InventoryCategory",
    "MovementType",
    "Sale",
    "SaleItem",
    "PaymentMethod",
    "Expense",
    "ExpenseCategory",
]