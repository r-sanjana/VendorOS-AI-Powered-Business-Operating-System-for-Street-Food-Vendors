"""
VendorOS - Dashboard Schemas
Structured response models for all dashboard analytics endpoints.
"""

from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import Field

from app.schemas.base import VendorOSSchema
from app.schemas.sales_schema import TopProduct


class DashboardSummary(VendorOSSchema):
    """High-level KPI snapshot for the dashboard home card."""

    vendor_id: str
    business_name: str
    total_revenue_today: Decimal
    total_revenue_month: Decimal
    total_expenses_month: Decimal
    net_profit_month: Decimal
    total_sales_today: int
    low_stock_items: int
    profit_margin_percent: float


class RevenueBreakdown(VendorOSSchema):
    """Revenue figures split by time horizon and payment method."""

    daily: Decimal
    weekly: Decimal
    monthly: Decimal
    by_payment_method: Dict[str, Decimal]


class ExpenseBreakdown(VendorOSSchema):
    """Expense totals split by category."""

    total: Decimal
    by_category: Dict[str, Decimal]


class ProfitSummary(VendorOSSchema):
    """Revenue vs expenses vs net profit."""

    revenue: Decimal
    expenses: Decimal
    gross_profit: Decimal
    profit_margin_percent: float


class TopProductsResponse(VendorOSSchema):
    """Ordered list of best-selling items."""

    period: str
    items: List[TopProduct]