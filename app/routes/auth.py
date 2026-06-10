"""
VendorOS - Authentication Routes
Handles /auth/register, /auth/login, /auth/me.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_id, get_db
from app.schemas.user_schema import AuthResponse, UserLoginRequest, UserRegisterRequest, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    payload: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    Create a new user account and return JWT tokens.

    - **name**: Full name (2–120 chars)
    - **email**: Unique email address
    - **password**: Min 8 chars, must contain a letter and a digit
    - **role**: ADMIN | VENDOR | EMPLOYEE | CUSTOMER
    """
    service = AuthService(db)
    return await service.register(payload)


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Authenticate and receive JWT tokens",
)
async def login(
    payload: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    Authenticate with email + password and receive access/refresh tokens.
    """
    service = AuthService(db)
    return await service.login(payload.email, payload.password)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get currently authenticated user's profile",
)
async def me(
    db: AsyncSession = Depends(get_db),
    user_id=Depends(get_current_user_id),
) -> UserResponse:
    """
    Return the profile of the user identified by the Bearer token.
    Requires: ``Authorization: Bearer <access_token>``
    """
    service = AuthService(db)
    return await service.get_current_user(user_id)