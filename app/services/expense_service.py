"""
VendorOS - Expense Service
Business logic for expense tracking and analytics.
"""

import math
from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.expense import ExpenseCategory
from app.repositories.expense_repository import ExpenseRepository
from app.schemas.base import PaginatedResponse
from app.schemas.expense_schema import (
    ExpenseAnalytics,
    ExpenseCreateRequest,
    ExpenseResponse,
    ExpenseUpdateRequest,
)


class ExpenseService:
    """Service layer for Expense management and analytics."""

    def __init__(self, db: AsyncSession) -> None:
        self._repo = ExpenseRepository(db)

    async def create_expense(self, data: ExpenseCreateRequest) -> ExpenseResponse:
        expense = await self._repo.create(**data.model_dump())
        return ExpenseResponse.model_validate(expense)

    async def list_expenses(
        self,
        vendor_id: UUID,
        page: int,
        size: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[ExpenseCategory] = None,
    ) -> PaginatedResponse[ExpenseResponse]:
        offset = (page - 1) * size
        expenses, total = await self._repo.get_by_vendor(
            vendor_id, offset, size, start_date, end_date, category
        )
        return PaginatedResponse(
            items=[ExpenseResponse.model_validate(e) for e in expenses],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    async def get_expense(self, expense_id: UUID) -> ExpenseResponse:
        expense = await self._repo.get_by_id(expense_id)
        if expense is None:
            raise NotFoundError("Expense", expense_id)
        return ExpenseResponse.model_validate(expense)

    async def update_expense(
        self, expense_id: UUID, data: ExpenseUpdateRequest
    ) -> ExpenseResponse:
        expense = await self._repo.update(
            expense_id, data.model_dump(exclude_none=True)
        )
        if expense is None:
            raise NotFoundError("Expense", expense_id)
        return ExpenseResponse.model_validate(expense)

    async def delete_expense(self, expense_id: UUID) -> None:
        deleted = await self._repo.delete(expense_id)
        if not deleted:
            raise NotFoundError("Expense", expense_id)

    # ── Analytics ──────────────────────────────────────────────────────────────

    async def expense_analytics(
        self, vendor_id: UUID, start_date: date, end_date: date
    ) -> List[ExpenseAnalytics]:
        rows = await self._repo.breakdown_by_category(vendor_id, start_date, end_date)
        return [ExpenseAnalytics(**row) for row in rows]