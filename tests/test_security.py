"""
VendorOS - Tests: Core Security
Unit tests for password hashing and JWT token lifecycle.
"""

import time
from datetime import timedelta

import pytest
from jose import JWTError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
    verify_token_type,
)


class TestPasswordHashing:
    """bcrypt hash / verify."""

    def test_hash_is_not_plaintext(self) -> None:
        hashed = hash_password("Secret123")
        assert hashed != "Secret123"
        assert hashed.startswith("$2b$")

    def test_correct_password_verifies(self) -> None:
        hashed = hash_password("MyPassword1")
        assert verify_password("MyPassword1", hashed) is True

    def test_wrong_password_fails(self) -> None:
        hashed = hash_password("Correct1")
        assert verify_password("Wrong1", hashed) is False

    def test_same_password_different_hashes(self) -> None:
        """bcrypt salts ensure two hashes of the same password differ."""
        h1 = hash_password("SamePass1")
        h2 = hash_password("SamePass1")
        assert h1 != h2
        assert verify_password("SamePass1", h1)
        assert verify_password("SamePass1", h2)


class TestJWTTokens:
    """JWT creation, decoding, and type verification."""

    def test_access_token_contains_subject(self) -> None:
        token = create_access_token(subject="user-123")
        payload = decode_token(token)
        assert payload["sub"] == "user-123"

    def test_access_token_type_claim(self) -> None:
        token = create_access_token(subject="user-abc")
        payload = decode_token(token)
        assert verify_token_type(payload, "access") is True
        assert verify_token_type(payload, "refresh") is False

    def test_refresh_token_type_claim(self) -> None:
        token = create_refresh_token(subject="user-xyz")
        payload = decode_token(token)
        assert verify_token_type(payload, "refresh") is True
        assert verify_token_type(payload, "access") is False

    def test_extra_claims_embedded(self) -> None:
        token = create_access_token(
            subject="user-456",
            extra_claims={"role": "VENDOR", "email": "test@test.com"},
        )
        payload = decode_token(token)
        assert payload["role"] == "VENDOR"
        assert payload["email"] == "test@test.com"

    def test_tampered_token_raises(self) -> None:
        token = create_access_token(subject="user-789")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(JWTError):
            decode_token(tampered)

    def test_garbage_token_raises(self) -> None:
        with pytest.raises(JWTError):
            decode_token("this.is.not.a.jwt")