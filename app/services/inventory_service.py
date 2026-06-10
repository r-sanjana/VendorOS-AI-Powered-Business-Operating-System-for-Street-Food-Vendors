"""
VendorOS - Inventory Service
Business logic for inventory and stock-movement management.
"""

import math
from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.inventory_repository import InventoryRepository
from app.schemas.base import PaginatedResponse
from app.schemas.inventory_schema import (
    InventoryItemCreateRequest,
    InventoryItemResponse,
    InventoryItemUpdateRequest,
    LowStockAlert,
    StockMovementCreateRequest,
    StockMovementResponse,
)


class InventoryService:
    """Service layer for Inventory management."""

    def __init__(self, db: AsyncSession) -> None:
        self._repo = InventoryRepository(db)

    async def create_item(
        self, data: InventoryItemCreateRequest
    ) -> InventoryItemResponse:
        item = await self._repo.create(**data.model_dump())
        return InventoryItemResponse.model_validate(item)

    async def list_items(
        self, vendor_id: UUID, page: int, size: int
    ) -> PaginatedResponse[InventoryItemResponse]:
        offset = (page - 1) * size
        items, total = await self._repo.get_by_vendor(vendor_id, offset, size)
        return PaginatedResponse(
            items=[InventoryItemResponse.model_validate(i) for i in items],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    async def get_item(self, item_id: UUID) -> InventoryItemResponse:
        item = await self._repo.get_by_id(item_id)
        if item is None:
            raise NotFoundError("InventoryItem", item_id)
        return InventoryItemResponse.model_validate(item)

    async def update_item(
        self, item_id: UUID, data: InventoryItemUpdateRequest
    ) -> InventoryItemResponse:
        item = await self._repo.update(item_id, data.model_dump(exclude_none=True))
        if item is None:
            raise NotFoundError("InventoryItem", item_id)
        return InventoryItemResponse.model_validate(item)

    async def delete_item(self, item_id: UUID) -> None:
        deleted = await self._repo.delete(item_id)
        if not deleted:
            raise NotFoundError("InventoryItem", item_id)

    async def record_movement(
        self, data: StockMovementCreateRequest
    ) -> StockMovementResponse:
        movement = await self._repo.apply_stock_movement(
            item_id=data.item_id,
            movement_type=data.movement_type,
            quantity=data.quantity,
            notes=data.notes,
        )
        return StockMovementResponse.model_validate(movement)

    async def get_low_stock_alerts(
        self, vendor_id: UUID
    ) -> List[LowStockAlert]:
        items = await self._repo.get_low_stock_items(vendor_id)
        return [
            LowStockAlert(
                item_id=item.id,
                item_name=item.name,
                current_stock=item.current_stock,
                reorder_level=item.reorder_level,
                unit=item.unit,
                category=item.category,
            )
            for item in items
        ]