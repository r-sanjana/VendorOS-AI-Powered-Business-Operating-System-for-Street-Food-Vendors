"""
VendorOS - Security Utilities
Handles password hashing (bcrypt) and JWT token lifecycle.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ── Password hashing ──────────────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of *plain_password*."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return ``True`` if *plain_password* matches *hashed_password*."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT helpers ───────────────────────────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_access_token(
    subject: str,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Mint a signed JWT access token.

    Parameters
    ----------
    subject:
        Typically the user's UUID string (``str(user.id)``).
    extra_claims:
        Optional dictionary of additional claims to embed (e.g. ``role``).

    Returns
    -------
    str
        Encoded JWT string.
    """
    expire = _utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": _utcnow(),
        "exp": expire,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """Mint a longer-lived refresh token."""
    expire = _utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": _utcnow(),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT.

    Raises
    ------
    JWTError
        If the token is invalid or expired.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def verify_token_type(payload: Dict[str, Any], expected_type: str) -> bool:
    """Return ``True`` if the ``type`` claim matches *expected_type*."""
    return payload.get("type") == expected_type