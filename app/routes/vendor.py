"""
VendorOS - Vendor Routes
CRUD for vendor profiles.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import PaginationParams, get_current_user_id, get_db
from app.schemas.base import PaginatedResponse
from app.schemas.vendor_schema import VendorCreateRequest, VendorResponse, VendorUpdateRequest
from app.services.vendor_service import VendorService

router = APIRouter(prefix="/vendors", tags=["Vendors"])


@router.post(
    "",
    response_model=VendorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a vendor profile",
)
async def create_vendor(
    payload: VendorCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> VendorResponse:
    """Create a new street-food vendor profile owned by the authenticated user."""
    return await VendorService(db).create_vendor(payload, user_id)


@router.get(
    "",
    response_model=PaginatedResponse[VendorResponse],
    summary="List all vendors (paginated)",
)
async def list_vendors(
    db: AsyncSession = Depends(get_db),
    pagination: PaginationParams = Depends(),
    _: UUID = Depends(get_current_user_id),
) -> PaginatedResponse[VendorResponse]:
    return await VendorService(db).list_vendors(pagination.page, pagination.size)


@router.get(
    "/{vendor_id}",
    response_model=VendorResponse,
    summary="Get a vendor by ID",
)
async def get_vendor(
    vendor_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> VendorResponse:
    return await VendorService(db).get_vendor(vendor_id)


@router.put(
    "/{vendor_id}",
    response_model=VendorResponse,
    summary="Update a vendor profile",
)
async def update_vendor(
    vendor_id: UUID,
    payload: VendorUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> VendorResponse:
    return await VendorService(db).update_vendor(vendor_id, payload, user_id)


@router.delete(
    "/{vendor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a vendor profile",
)
async def delete_vendor(
    vendor_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> None:
    await VendorService(db).delete_vendor(vendor_id, user_id)