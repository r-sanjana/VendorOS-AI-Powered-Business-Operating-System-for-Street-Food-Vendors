"""
VendorOS - Sales Repository
Data-access layer for Sale / SaleItem with analytics queries.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.sales import Sale, SaleItem
from app.repositories.base_repository import BaseRepository


class SalesRepository(BaseRepository[Sale]):
    """Repository for Sale entity."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Sale, db)

    # ── Queries ────────────────────────────────────────────────────────────────

    async def get_with_items(self, sale_id: UUID) -> Optional[Sale]:
        """Return a Sale with its SaleItems eagerly loaded."""
        result = await self.db.execute(
            select(Sale)
            .options(selectinload(Sale.items))
            .where(Sale.id == sale_id)
        )
        return result.scalar_one_or_none()

    async def get_by_vendor(
        self,
        vendor_id: UUID,
        offset: int = 0,
        limit: int = 20,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Tuple[List[Sale], int]:
        """Paginated sales for a vendor with optional date filtering."""
        filters = [Sale.vendor_id == vendor_id]
        if start_date:
            filters.append(Sale.sale_date >= start_date)
        if end_date:
            filters.append(Sale.sale_date <= end_date)
        return await self.get_all(offset=offset, limit=limit, filters=filters)

    # ── Revenue analytics ──────────────────────────────────────────────────────

    async def revenue_for_period(
        self, vendor_id: UUID, start_date: date, end_date: date
    ) -> Decimal:
        """Sum of ``total_amount`` in [start_date, end_date]."""
        result = await self.db.execute(
            select(func.coalesce(func.sum(Sale.total_amount), 0)).where(
                Sale.vendor_id == vendor_id,
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
            )
        )
        return result.scalar_one()

    async def daily_revenue(self, vendor_id: UUID, day: date) -> Decimal:
        return await self.revenue_for_period(vendor_id, day, day)

    async def weekly_revenue(self, vendor_id: UUID, reference_date: date) -> Decimal:
        start = reference_date - timedelta(days=reference_date.weekday())
        end = start + timedelta(days=6)
        return await self.revenue_for_period(vendor_id, start, end)

    async def monthly_revenue(self, vendor_id: UUID, year: int, month: int) -> Decimal:
        start = date(year, month, 1)
        # last day of month
        if month == 12:
            end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(year, month + 1, 1) - timedelta(days=1)
        return await self.revenue_for_period(vendor_id, start, end)

    async def transaction_count(
        self, vendor_id: UUID, start_date: date, end_date: date
    ) -> int:
        result = await self.db.execute(
            select(func.count(Sale.id)).where(
                Sale.vendor_id == vendor_id,
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
            )
        )
        return result.scalar_one()

    # ── Top products ───────────────────────────────────────────────────────────

    async def top_products(
        self,
        vendor_id: UUID,
        start_date: date,
        end_date: date,
        top_n: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Return top *top_n* items by total quantity sold in the given period.
        Joins Sale → SaleItem and aggregates.
        """
        result = await self.db.execute(
            select(
                SaleItem.item_name,
                func.sum(SaleItem.quantity).label("total_quantity"),
                func.sum(SaleItem.quantity * SaleItem.unit_price).label("total_revenue"),
            )
            .join(Sale, SaleItem.sale_id == Sale.id)
            .where(
                Sale.vendor_id == vendor_id,
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
            )
            .group_by(SaleItem.item_name)
            .order_by(func.sum(SaleItem.quantity).desc())
            .limit(top_n)
        )
        rows = result.all()
        return [
            {
                "item_name": r.item_name,
                "total_quantity": int(r.total_quantity),
                "total_revenue": Decimal(str(r.total_revenue)),
            }
            for r in rows
        ]

    # ── Payment method breakdown ───────────────────────────────────────────────

    async def revenue_by_payment_method(
        self, vendor_id: UUID, start_date: date, end_date: date
    ) -> Dict[str, Decimal]:
        """Return a dict of {payment_method: total_amount}."""
        result = await self.db.execute(
            select(
                Sale.payment_method,
                func.coalesce(func.sum(Sale.total_amount), 0).label("total"),
            )
            .where(
                Sale.vendor_id == vendor_id,
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
            )
            .group_by(Sale.payment_method)
        )
        return {str(r.payment_method.value): Decimal(str(r.total)) for r in result.all()}