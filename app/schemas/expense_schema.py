"""
VendorOS - Expense Schemas
Request / Response Pydantic models for the Expense domain.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.models.expense import ExpenseCategory
from app.schemas.base import VendorOSSchema


class ExpenseCreateRequest(VendorOSSchema):
    vendor_id: UUID
    expense_date: date
    category: ExpenseCategory = ExpenseCategory.OTHER
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=1000)
    receipt_url: Optional[str] = Field(None, max_length=512)


class ExpenseUpdateRequest(VendorOSSchema):
    expense_date: Optional[date] = None
    category: Optional[ExpenseCategory] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=1000)
    receipt_url: Optional[str] = Field(None, max_length=512)


class ExpenseResponse(VendorOSSchema):
    id: UUID
    vendor_id: UUID
    expense_date: date
    category: ExpenseCategory
    amount: Decimal
    description: Optional[str]
    receipt_url: Optional[str]
    created_at: datetime
    updated_at: datetime


class ExpenseAnalytics(VendorOSSchema):
    """Aggregated expense analytics per category."""

    category: ExpenseCategory
    total_amount: Decimal
    transaction_count: int
    percentage_of_total: float