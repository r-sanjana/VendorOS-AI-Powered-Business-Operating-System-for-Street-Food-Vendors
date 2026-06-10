"""
VendorOS - Dashboard Routes
Aggregated analytics endpoints for the vendor dashboard.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_id, get_db
from app.schemas.dashboard_schema import (
    DashboardSummary,
    ExpenseBreakdown,
    ProfitSummary,
    RevenueBreakdown,
    TopProductsResponse,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="High-level KPI snapshot (today + month-to-date)",
)
async def dashboard_summary(
    vendor_id: UUID = Query(..., description="Vendor UUID"),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> DashboardSummary:
    """
    Returns today's revenue, month-to-date revenue and expenses, net profit,
    number of sales today, and count of low-stock items.
    """
    return await DashboardService(db).get_summary(vendor_id)


@router.get(
    "/revenue",
    response_model=RevenueBreakdown,
    summary="Revenue breakdown: daily / weekly / monthly + by payment method",
)
async def dashboard_revenue(
    vendor_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> RevenueBreakdown:
    return await DashboardService(db).get_revenue(vendor_id)


@router.get(
    "/expenses",
    response_model=ExpenseBreakdown,
    summary="Expense breakdown by category (current month)",
)
async def dashboard_expenses(
    vendor_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> ExpenseBreakdown:
    return await DashboardService(db).get_expenses(vendor_id)


@router.get(
    "/profit",
    response_model=ProfitSummary,
    summary="Revenue vs expenses vs net profit (current month)",
)
async def dashboard_profit(
    vendor_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> ProfitSummary:
    return await DashboardService(db).get_profit(vendor_id)


@router.get(
    "/top-products",
    response_model=TopProductsResponse,
    summary="Top-selling products (current month)",
)
async def dashboard_top_products(
    vendor_id: UUID = Query(...),
    top_n: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> TopProductsResponse:
    return await DashboardService(db).get_top_products(vendor_id, top_n)