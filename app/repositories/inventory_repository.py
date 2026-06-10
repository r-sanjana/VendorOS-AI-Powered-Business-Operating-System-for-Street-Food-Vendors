"""
VendorOS - Inventory Repository
Data-access layer for InventoryItem and StockMovement.
"""

from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryItem, MovementType, StockMovement
from app.repositories.base_repository import BaseRepository


class InventoryRepository(BaseRepository[InventoryItem]):
    """Repository for InventoryItem entity."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(InventoryItem, db)

    async def get_by_vendor(
        self, vendor_id: UUID, offset: int = 0, limit: int = 20
    ) -> Tuple[List[InventoryItem], int]:
        """Return paginated inventory items for a specific vendor."""
        return await self.get_all(
            offset=offset,
            limit=limit,
            filters=[InventoryItem.vendor_id == vendor_id],
        )

    async def get_low_stock_items(self, vendor_id: UUID) -> List[InventoryItem]:
        """Return all items where current_stock ≤ reorder_level."""
        result = await self.db.execute(
            select(InventoryItem).where(
                InventoryItem.vendor_id == vendor_id,
                InventoryItem.current_stock <= InventoryItem.reorder_level,
            )
        )
        return list(result.scalars().all())

    async def apply_stock_movement(
        self,
        item_id: UUID,
        movement_type: MovementType,
        quantity: Decimal,
        notes: Optional[str] = None,
    ) -> StockMovement:
        """
        Adjust the item's ``current_stock`` and persist a StockMovement record.

        - IN / ADJUST-positive → adds to stock
        - OUT / WASTE → subtracts from stock
        """
        item = await self.get_by_id(item_id)
        if item is None:
            raise ValueError(f"InventoryItem {item_id} not found")

        if movement_type == MovementType.IN:
            item.current_stock += quantity
        elif movement_type in (MovementType.OUT, MovementType.WASTE):
            item.current_stock = max(Decimal("0"), item.current_stock - quantity)
        else:  # ADJUST – signed quantity
            item.current_stock = max(Decimal("0"), item.current_stock + quantity)

        self.db.add(item)

        movement = StockMovement(
            item_id=item_id,
            movement_type=movement_type,
            quantity=quantity,
            notes=notes,
        )
        self.db.add(movement)
        await self.db.flush()
        await self.db.refresh(movement)
        return movement