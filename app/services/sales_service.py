"""
VendorOS - Sales Service
Business logic for sales recording and revenue analytics.
"""

import math
from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.sales import SaleItem
from app.repositories.sales_repository import SalesRepository
from app.schemas.base import PaginatedResponse
from app.schemas.sales_schema import (
    RevenueSummary,
    SaleCreateRequest,
    SaleResponse,
    TopProduct,
)


class SalesService:
    """Service layer for Sales management and analytics."""

    def __init__(self, db: AsyncSession) -> None:
        self._repo = SalesRepository(db)

    async def create_sale(self, data: SaleCreateRequest) -> SaleResponse:
        """
        Persist a new Sale with its line items.
        Computes ``total_amount`` from the supplied items.
        """
        total = sum(
            Decimal(str(item.quantity)) * item.unit_price for item in data.items
        )
        sale = await self._repo.create(
            vendor_id=data.vendor_id,
            sale_date=data.sale_date,
            payment_method=data.payment_method,
            total_amount=total,
            notes=data.notes,
        )
        for item_data in data.items:
            self._repo.db.add(
                SaleItem(
                    sale_id=sale.id,
                    item_name=item_data.item_name,
                    quantity=item_data.quantity,
                    unit_price=item_data.unit_price,
                )
            )
        await self._repo.db.flush()
        full_sale = await self._repo.get_with_items(sale.id)
        return SaleResponse.model_validate(full_sale)

    async def list_sales(
        self,
        vendor_id: UUID,
        page: int,
        size: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> PaginatedResponse[SaleResponse]:
        offset = (page - 1) * size
        sales, total = await self._repo.get_by_vendor(
            vendor_id, offset, size, start_date, end_date
        )
        return PaginatedResponse(
            items=[SaleResponse.model_validate(s) for s in sales],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    async def get_sale(self, sale_id: UUID) -> SaleResponse:
        sale = await self._repo.get_with_items(sale_id)
        if sale is None:
            raise NotFoundError("Sale", sale_id)
        return SaleResponse.model_validate(sale)

    # ── Analytics ──────────────────────────────────────────────────────────────

    async def revenue_summary(
        self, vendor_id: UUID, start_date: date, end_date: date
    ) -> RevenueSummary:
        total = await self._repo.revenue_for_period(vendor_id, start_date, end_date)
        count = await self._repo.transaction_count(vendor_id, start_date, end_date)
        return RevenueSummary(
            period=f"{start_date} – {end_date}",
            total_revenue=total,
            transaction_count=count,
        )

    async def top_products(
        self,
        vendor_id: UUID,
        start_date: date,
        end_date: date,
        top_n: int = 10,
    ) -> List[TopProduct]:
        rows = await self._repo.top_products(vendor_id, start_date, end_date, top_n)
        return [TopProduct(**row) for row in rows]