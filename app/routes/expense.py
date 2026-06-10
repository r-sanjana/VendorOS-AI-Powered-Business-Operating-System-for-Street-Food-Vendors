"""
VendorOS - Expense Routes
Track vendor expenses and view analytics by category.
"""

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import PaginationParams, get_current_user_id, get_db
from app.models.expense import ExpenseCategory
from app.schemas.base import PaginatedResponse
from app.schemas.expense_schema import (
    ExpenseAnalytics,
    ExpenseCreateRequest,
    ExpenseResponse,
    ExpenseUpdateRequest,
)
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post(
    "",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new expense",
)
async def create_expense(
    payload: ExpenseCreateRequest,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> ExpenseResponse:
    return await ExpenseService(db).create_expense(payload)


@router.get(
    "",
    response_model=PaginatedResponse[ExpenseResponse],
    summary="List expenses for a vendor",
)
async def list_expenses(
    vendor_id: UUID = Query(...),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    category: Optional[ExpenseCategory] = Query(None),
    db: AsyncSession = Depends(get_db),
    pagination: PaginationParams = Depends(),
    _: UUID = Depends(get_current_user_id),
) -> PaginatedResponse[ExpenseResponse]:
    return await ExpenseService(db).list_expenses(
        vendor_id, pagination.page, pagination.size,
        start_date, end_date, category
    )


@router.get(
    "/analytics",
    response_model=List[ExpenseAnalytics],
    summary="Expense breakdown by category for a date range",
)
async def expense_analytics(
    vendor_id: UUID = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> List[ExpenseAnalytics]:
    return await ExpenseService(db).expense_analytics(vendor_id, start_date, end_date)


@router.get(
    "/{expense_id}",
    response_model=ExpenseResponse,
    summary="Get a single expense record",
)
async def get_expense(
    expense_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> ExpenseResponse:
    return await ExpenseService(db).get_expense(expense_id)


@router.put(
    "/{expense_id}",
    response_model=ExpenseResponse,
    summary="Update an expense record",
)
async def update_expense(
    expense_id: UUID,
    payload: ExpenseUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> ExpenseResponse:
    return await ExpenseService(db).update_expense(expense_id, payload)


@router.delete(
    "/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an expense record",
)
async def delete_expense(
    expense_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> None:
    await ExpenseService(db).delete_expense(expense_id)