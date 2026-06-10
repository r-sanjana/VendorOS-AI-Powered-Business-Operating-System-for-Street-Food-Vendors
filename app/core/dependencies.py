"""
VendorOS - FastAPI Dependency Injection
Provides reusable ``Depends``-compatible callables for auth, pagination, and DB.
"""

from typing import AsyncGenerator, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token, verify_token_type
from app.database.connection import AsyncSessionLocal
from app.models.user import UserRole

# ── Database ──────────────────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session; always closed after request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Auth bearer extraction ────────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=True)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> UUID:
    """
    Validate the ``Authorization: Bearer <token>`` header and return the
    authenticated user's UUID.

    Raises
    ------
    HTTPException 401
        On missing, expired, or malformed token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
        if not verify_token_type(payload, "access"):
            raise credentials_exception
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return UUID(user_id)
    except (JWTError, ValueError):
        raise credentials_exception


def require_role(*roles: UserRole):
    """
    Factory that returns a dependency which enforces one of the given roles.

    Usage::

        @router.delete("/vendors/{id}", dependencies=[Depends(require_role(UserRole.ADMIN))])
    """
    async def _check(
        db: AsyncSession = Depends(get_db),
        user_id: UUID = Depends(get_current_user_id),
    ) -> UUID:
        from app.repositories.user_repository import UserRepository
        repo = UserRepository(db)
        user = await repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {[r.value for r in roles]}",
            )
        return user_id

    return _check


# ── Pagination ─────────────────────────────────────────────────────────────────

class PaginationParams:
    """Common query-string pagination parameters."""

    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number (1-based)"),
        size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    ) -> None:
        self.page = page
        self.size = size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size