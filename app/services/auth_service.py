"""
VendorOS - Authentication Service
Business logic for user registration, login, and profile retrieval.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    DuplicateEmailError,
    InactiveUserError,
    InvalidCredentialsError,
    NotFoundError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import (
    AuthResponse,
    TokenResponse,
    UserRegisterRequest,
    UserResponse,
)


class AuthService:
    """
    Handles registration, login and identity retrieval.

    All business rules (uniqueness, password verification, token minting) live
    here; the repository layer handles only raw DB operations.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._repo = UserRepository(db)

    async def register(self, data: UserRegisterRequest) -> AuthResponse:
        """
        Create a new user account.

        Raises
        ------
        DuplicateEmailError
            If the email is already registered.
        """
        if await self._repo.email_exists(data.email.lower()):
            raise DuplicateEmailError(data.email)

        user = await self._repo.create(
            name=data.name,
            email=data.email.lower(),
            phone=data.phone,
            password_hash=hash_password(data.password),
            role=data.role,
            is_active=True,
        )
        return self._build_auth_response(user)

    async def login(self, email: str, password: str) -> AuthResponse:
        """
        Authenticate a user and return tokens.

        Raises
        ------
        InvalidCredentialsError
            If email/password pair is incorrect.
        InactiveUserError
            If the account is deactivated.
        """
        user = await self._repo.get_by_email(email.lower())
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
        if not user.is_active:
            raise InactiveUserError()
        return self._build_auth_response(user)

    async def get_current_user(self, user_id: UUID) -> UserResponse:
        """
        Return the public profile of the authenticated user.

        Raises
        ------
        NotFoundError
            If the user_id is not found (should not normally happen).
        """
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User", user_id)
        return UserResponse.model_validate(user)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _build_auth_response(user: User) -> AuthResponse:
        """Mint tokens and construct the full AuthResponse."""
        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"role": user.role.value, "email": user.email},
        )
        refresh_token = create_refresh_token(subject=str(user.id))
        tokens = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        return AuthResponse(
            user=UserResponse.model_validate(user),
            tokens=tokens,
        )