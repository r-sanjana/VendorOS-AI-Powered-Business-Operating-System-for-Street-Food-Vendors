"""
VendorOS - Vendor Repository
Data-access layer for the Vendor model.
"""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.vendor import Vendor
from app.repositories.base_repository import BaseRepository


class VendorRepository(BaseRepository[Vendor]):
    """Repository for Vendor entity."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Vendor, db)

    async def get_by_owner_id(self, owner_id: UUID) -> Optional[Vendor]:
        """Return the vendor profile for a given owner (user) id."""
        result = await self.db.execute(
            select(Vendor).where(Vendor.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    async def get_all_vendors(
        self, offset: int = 0, limit: int = 20
    ) -> Tuple[List[Vendor], int]:
        """Paginated list of all vendors."""
        return await self.get_all(offset=offset, limit=limit)