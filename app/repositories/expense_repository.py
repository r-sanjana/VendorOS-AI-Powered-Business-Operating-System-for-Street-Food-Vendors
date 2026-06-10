"""
VendorOS - Expense Repository
Data-access layer for Expense with analytics queries.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import Expense, ExpenseCategory
from app.repositories.base_repository import BaseRepository


class ExpenseRepository(BaseRepository[Expense]):
    """Repository for Expense entity."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Expense, db)

    async def get_by_vendor(
        self,
        vendor_id: UUID,
        offset: int = 0,
        limit: int = 20,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[ExpenseCategory] = None,
    ) -> Tuple[List[Expense], int]:
        """Paginated expenses for a vendor with optional filters."""
        filters = [Expense.vendor_id == vendor_id]
        if start_date:
            filters.append(Expense.expense_date >= start_date)
        if end_date:
            filters.append(Expense.expense_date <= end_date)
        if category:
            filters.append(Expense.category == category)
        return await self.get_all(offset=offset, limit=limit, filters=filters)

    async def total_for_period(
        self, vendor_id: UUID, start_date: date, end_date: date
    ) -> Decimal:
        """Sum of all expenses in the given date range."""
        result = await self.db.execute(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(
                Expense.vendor_id == vendor_id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
        )
        return result.scalar_one()

    async def monthly_total(
        self, vendor_id: UUID, year: int, month: int
    ) -> Decimal:
        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(year, month + 1, 1) - timedelta(days=1)
        return await self.total_for_period(vendor_id, start, end)

    async def breakdown_by_category(
        self, vendor_id: UUID, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """Return per-category totals and counts in the period."""
        result = await self.db.execute(
            select(
                Expense.category,
                func.sum(Expense.amount).label("total"),
                func.count(Expense.id).label("count"),
            )
            .where(
                Expense.vendor_id == vendor_id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
            .group_by(Expense.category)
            .order_by(func.sum(Expense.amount).desc())
        )
        rows = result.all()
        total_all = sum(Decimal(str(r.total)) for r in rows) or Decimal("1")
        return [
            {
                "category": r.category,
                "total_amount": Decimal(str(r.total)),
                "transaction_count": int(r.count),
                "percentage_of_total": float(
                    (Decimal(str(r.total)) / total_all * 100).quantize(Decimal("0.01"))
                ),
            }
            for r in rows
        ]