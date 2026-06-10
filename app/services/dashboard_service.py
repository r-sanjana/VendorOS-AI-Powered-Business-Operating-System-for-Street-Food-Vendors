"""
VendorOS - Dashboard Service
Aggregates revenue, expense, and profit data for dashboard endpoints.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.expense_repository import ExpenseRepository
from app.repositories.sales_repository import SalesRepository
from app.repositories.vendor_repository import VendorRepository
from app.repositories.inventory_repository import InventoryRepository
from app.schemas.dashboard_schema import (
    DashboardSummary,
    ExpenseBreakdown,
    ProfitSummary,
    RevenueBreakdown,
    TopProductsResponse,
)
from app.schemas.sales_schema import TopProduct


class DashboardService:
    """Computes all dashboard KPI data."""

    def __init__(self, db: AsyncSession) -> None:
        self._sales = SalesRepository(db)
        self._expenses = ExpenseRepository(db)
        self._vendors = VendorRepository(db)
        self._inventory = InventoryRepository(db)

    async def get_summary(self, vendor_id: UUID) -> DashboardSummary:
        """Return high-level KPI snapshot."""
        vendor = await self._vendors.get_by_id(vendor_id)
        if vendor is None:
            raise NotFoundError("Vendor", vendor_id)

        today = date.today()
        month_start = today.replace(day=1)

        revenue_today = await self._sales.daily_revenue(vendor_id, today)
        revenue_month = await self._sales.revenue_for_period(vendor_id, month_start, today)
        expenses_month = await self._expenses.total_for_period(vendor_id, month_start, today)
        net_profit_month = revenue_month - expenses_month
        sales_today = await self._sales.transaction_count(vendor_id, today, today)

        low_stock_items = await self._inventory.get_low_stock_items(vendor_id)

        profit_margin = (
            float((net_profit_month / revenue_month * 100).quantize(Decimal("0.01")))
            if revenue_month > 0
            else 0.0
        )

        return DashboardSummary(
            vendor_id=str(vendor_id),
            business_name=vendor.business_name,
            total_revenue_today=revenue_today,
            total_revenue_month=revenue_month,
            total_expenses_month=expenses_month,
            net_profit_month=net_profit_month,
            total_sales_today=sales_today,
            low_stock_items=len(low_stock_items),
            profit_margin_percent=profit_margin,
        )

    async def get_revenue(self, vendor_id: UUID) -> RevenueBreakdown:
        today = date.today()
        month_start = today.replace(day=1)
        week_start = today - timedelta(days=today.weekday())

        daily = await self._sales.daily_revenue(vendor_id, today)
        weekly = await self._sales.revenue_for_period(vendor_id, week_start, today)
        monthly = await self._sales.revenue_for_period(vendor_id, month_start, today)
        by_method = await self._sales.revenue_by_payment_method(
            vendor_id, month_start, today
        )

        return RevenueBreakdown(
            daily=daily, weekly=weekly, monthly=monthly,
            by_payment_method=by_method,
        )

    async def get_expenses(self, vendor_id: UUID) -> ExpenseBreakdown:
        today = date.today()
        month_start = today.replace(day=1)
        total = await self._expenses.total_for_period(vendor_id, month_start, today)
        breakdown = await self._expenses.breakdown_by_category(
            vendor_id, month_start, today
        )
        by_cat = {str(row["category"].value): row["total_amount"] for row in breakdown}
        return ExpenseBreakdown(total=total, by_category=by_cat)

    async def get_profit(self, vendor_id: UUID) -> ProfitSummary:
        today = date.today()
        month_start = today.replace(day=1)
        revenue = await self._sales.revenue_for_period(vendor_id, month_start, today)
        expenses = await self._expenses.total_for_period(vendor_id, month_start, today)
        gross = revenue - expenses
        margin = float((gross / revenue * 100).quantize(Decimal("0.01"))) if revenue > 0 else 0.0
        return ProfitSummary(
            revenue=revenue, expenses=expenses,
            gross_profit=gross, profit_margin_percent=margin,
        )

    async def get_top_products(
        self, vendor_id: UUID, top_n: int = 10
    ) -> TopProductsResponse:
        today = date.today()
        month_start = today.replace(day=1)
        rows = await self._sales.top_products(vendor_id, month_start, today, top_n)
        return TopProductsResponse(
            period=f"{month_start} – {today}",
            items=[TopProduct(**row) for row in rows],
        )