"""
VendorOS - Vendor Service
Business logic for vendor CRUD operations.
"""

import math
from typing import Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.user import UserRole
from app.repositories.user_repository import UserRepository
from app.repositories.vendor_repository import VendorRepository
from app.schemas.base import PaginatedResponse
from app.schemas.vendor_schema import (
    VendorCreateRequest,
    VendorResponse,
    VendorUpdateRequest,
)


class VendorService:
    """Service layer for Vendor management."""

    def __init__(self, db: AsyncSession) -> None:
        self._repo = VendorRepository(db)
        self._user_repo = UserRepository(db)

    async def create_vendor(
        self, data: VendorCreateRequest, requesting_user_id: UUID
    ) -> VendorResponse:
        """
        Create a vendor profile.

        The requesting user must exist and ideally hold the VENDOR role.
        """
        vendor = await self._repo.create(
            **data.model_dump(exclude_none=False),
            owner_id=requesting_user_id,
        )
        return VendorResponse.model_validate(vendor)

    async def list_vendors(
        self, page: int, size: int
    ) -> PaginatedResponse[VendorResponse]:
        offset = (page - 1) * size
        vendors, total = await self._repo.get_all_vendors(offset=offset, limit=size)
        return PaginatedResponse(
            items=[VendorResponse.model_validate(v) for v in vendors],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    async def get_vendor(self, vendor_id: UUID) -> VendorResponse:
        vendor = await self._repo.get_by_id(vendor_id)
        if vendor is None:
            raise NotFoundError("Vendor", vendor_id)
        return VendorResponse.model_validate(vendor)

    async def update_vendor(
        self,
        vendor_id: UUID,
        data: VendorUpdateRequest,
        requesting_user_id: UUID,
    ) -> VendorResponse:
        vendor = await self._repo.get_by_id(vendor_id)
        if vendor is None:
            raise NotFoundError("Vendor", vendor_id)
        # Only the owner or an ADMIN may update
        user = await self._user_repo.get_by_id(requesting_user_id)
        if user and user.role != UserRole.ADMIN and vendor.owner_id != requesting_user_id:
            raise ForbiddenError("Only the vendor owner can update this profile")

        updated = await self._repo.update(
            vendor_id, data.model_dump(exclude_none=True)
        )
        return VendorResponse.model_validate(updated)

    async def delete_vendor(
        self, vendor_id: UUID, requesting_user_id: UUID
    ) -> None:
        vendor = await self._repo.get_by_id(vendor_id)
        if vendor is None:
            raise NotFoundError("Vendor", vendor_id)
        user = await self._user_repo.get_by_id(requesting_user_id)
        if user and user.role != UserRole.ADMIN and vendor.owner_id != requesting_user_id:
            raise ForbiddenError("Only the vendor owner can delete this profile")
        await self._repo.delete(vendor_id)