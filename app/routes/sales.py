"""
VendorOS - Sales Routes
Record sales transactions and query revenue analytics.
"""

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import PaginationParams, get_current_user_id, get_db
from app.schemas.base import PaginatedResponse
from app.schemas.sales_schema import (
    RevenueSummary,
    SaleCreateRequest,
    SaleResponse,
    TopProduct,
)
from app.services.sales_service import SalesService

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.post(
    "",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new sale",
)
async def create_sale(
    payload: SaleCreateRequest,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> SaleResponse:
    return await SalesService(db).create_sale(payload)


@router.get(
    "",
    response_model=PaginatedResponse[SaleResponse],
    summary="List sales for a vendor",
)
async def list_sales(
    vendor_id: UUID = Query(...),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    pagination: PaginationParams = Depends(),
    _: UUID = Depends(get_current_user_id),
) -> PaginatedResponse[SaleResponse]:
    return await SalesService(db).list_sales(
        vendor_id, pagination.page, pagination.size, start_date, end_date
    )


@router.get(
    "/{sale_id}",
    response_model=SaleResponse,
    summary="Get a sale by ID (with line items)",
)
async def get_sale(
    sale_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> SaleResponse:
    return await SalesService(db).get_sale(sale_id)


@router.get(
    "/analytics/revenue",
    response_model=RevenueSummary,
    summary="Revenue summary for a date range",
)
async def revenue_summary(
    vendor_id: UUID = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> RevenueSummary:
    return await SalesService(db).revenue_summary(vendor_id, start_date, end_date)


@router.get(
    "/analytics/top-products",
    response_model=List[TopProduct],
    summary="Top-selling products in a date range",
)
async def top_products(
    vendor_id: UUID = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    top_n: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> List[TopProduct]:
    return await SalesService(db).top_products(vendor_id, start_date, end_date, top_n)