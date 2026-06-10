"""
VendorOS - Inventory Routes
CRUD for inventory items plus stock-movement and low-stock alert endpoints.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import PaginationParams, get_current_user_id, get_db
from app.schemas.base import PaginatedResponse
from app.schemas.inventory_schema import (
    InventoryItemCreateRequest,
    InventoryItemResponse,
    InventoryItemUpdateRequest,
    LowStockAlert,
    StockMovementCreateRequest,
    StockMovementResponse,
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.post(
    "",
    response_model=InventoryItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an inventory item",
)
async def create_item(
    payload: InventoryItemCreateRequest,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> InventoryItemResponse:
    return await InventoryService(db).create_item(payload)


@router.get(
    "",
    response_model=PaginatedResponse[InventoryItemResponse],
    summary="List inventory items for a vendor",
)
async def list_items(
    vendor_id: UUID = Query(..., description="Vendor UUID"),
    db: AsyncSession = Depends(get_db),
    pagination: PaginationParams = Depends(),
    _: UUID = Depends(get_current_user_id),
) -> PaginatedResponse[InventoryItemResponse]:
    return await InventoryService(db).list_items(vendor_id, pagination.page, pagination.size)


@router.get(
    "/low-stock",
    response_model=List[LowStockAlert],
    summary="Get items below reorder level",
)
async def low_stock_alerts(
    vendor_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> List[LowStockAlert]:
    return await InventoryService(db).get_low_stock_alerts(vendor_id)


@router.get(
    "/{item_id}",
    response_model=InventoryItemResponse,
    summary="Get a single inventory item",
)
async def get_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> InventoryItemResponse:
    return await InventoryService(db).get_item(item_id)


@router.put(
    "/{item_id}",
    response_model=InventoryItemResponse,
    summary="Update an inventory item",
)
async def update_item(
    item_id: UUID,
    payload: InventoryItemUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> InventoryItemResponse:
    return await InventoryService(db).update_item(item_id, payload)


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an inventory item",
)
async def delete_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> None:
    await InventoryService(db).delete_item(item_id)


@router.post(
    "/movements",
    response_model=StockMovementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a stock movement (IN/OUT/WASTE/ADJUST)",
)
async def record_movement(
    payload: StockMovementCreateRequest,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> StockMovementResponse:
    return await InventoryService(db).record_movement(payload)