"""
VendorOS - Tests: Authentication
Covers POST /auth/register, POST /auth/login, GET /auth/me.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio


class TestRegister:
    """POST /api/v1/auth/register"""

    async def test_register_success(self, client: AsyncClient) -> None:
        """New user registers successfully and receives tokens."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "name": "Ravi Kumar",
                "email":"ravi@example.com",
                "password": "Secret123",
                "role": "VENDOR",
            },
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["user"]["email"] == "ravi@example.com"
        assert data["user"]["role"] == "VENDOR"
        assert "access_token" in data["tokens"]
        assert "password_hash" not in str(data)  # never leak the hash

    async def test_register_duplicate_email(self, client: AsyncClient) -> None:
        """Registering with an existing email returns 400."""
        payload = {
            "name": "User A",
            "email": "login@example.com",
            "password": "Pass1234",
            "role": "CUSTOMER",
        }
        await client.post("/api/v1/auth/register", json=payload)
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 400
        assert "already registered" in resp.json()["message"].lower()

    async def test_register_weak_password(self, client: AsyncClient) -> None:
        """Password with no digits is rejected with 422."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "name": "Bad Pass",
                "email": "badpass@example.com",
                "password": "nodigitshere",
                "role": "CUSTOMER",
            },
        )
        assert resp.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient) -> None:
        """Malformed email is rejected with 422."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={"name": "X", "email": "not-an-email", "password": "Pass123"},
        )
        assert resp.status_code == 422


class TestLogin:
    """POST /api/v1/auth/login"""

    async def test_login_success(self, client: AsyncClient) -> None:
        """Correct credentials return 200 with access + refresh tokens."""
        await client.post(
            "/api/v1/auth/register",
            json={"name": "Login Test", "email": "login@example.com", "password": "Login123"},
        )
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "Login123"},
        )
        assert resp.status_code == 200
        tokens = resp.json()["tokens"]
        assert tokens["token_type"] == "bearer"
        assert tokens["access_token"]
        assert tokens["refresh_token"]

    async def test_login_wrong_password(self, client: AsyncClient) -> None:
        """Wrong password returns 401."""
        await client.post(
            "/api/v1/auth/register",
            json={"name": "Wrong Pass", "email": "ghost@example.com", "password": "Correct1"},
        )
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "wrongpass@example.com", "password": "WrongPass1"},
        )
        assert resp.status_code == 401

    async def test_login_unknown_email(self, client: AsyncClient) -> None:
        """Unknown email returns 401."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "Ghost1234"},
        )
        assert resp.status_code == 401


class TestMe:
    """GET /api/v1/auth/me"""

    async def test_me_authenticated(self, client: AsyncClient) -> None:
        """Authenticated user receives their own profile."""
        register = await client.post(
            "/api/v1/auth/register",
            json={
                "name": "Me Test",
                "email": "me@example.com",
                "password": "MeTest123",
                "role": "CUSTOMER",
            },
        )

        print("REGISTER:", register.status_code)
        print(register.json())

        assert register.status_code == 201

        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "me@example.com", "password": "MeTest123"},
        )
        print(login.status_code)
        print(login.json())
        token = login.json()["tokens"]["access_token"]
        resp = await client.get("/api/v1/auth/me", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.json()["email"] == "me@example.com"

    async def test_me_unauthenticated(self, client: AsyncClient) -> None:
        """Request without token returns 403 (no bearer)."""
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 403

    async def test_me_invalid_token(self, client: AsyncClient) -> None:
        """Malformed token returns 401."""
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer this.is.garbage"},
        )
        assert resp.status_code == 401