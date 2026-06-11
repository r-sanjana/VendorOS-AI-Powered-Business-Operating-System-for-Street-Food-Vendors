"""
VendorOS - Test Configuration & Fixtures
Provides an async test client, in-memory SQLite database,
and reusable fixtures for every test module.
"""

from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.database.connection import Base
from app.main import app
from app.models.user import User, UserRole
from app.core.dependencies import get_db

# ── Use an in-memory SQLite DB for tests ──────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# ── Database setup / teardown ─────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create all tables, yield a fresh session, then drop all tables.
    Each test function gets a clean slate.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── Override the DB dependency ────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Return an async HTTPX test client wired to the in-memory test database.
    The ``get_db`` dependency is overridden so every request uses the same
    test session.
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Seed users ────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Seed and return an ADMIN user."""
    user = User(
        name="Admin User",
        email="admin@example.com",
        password_hash=hash_password("Admin1234"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def vendor_user(db_session: AsyncSession) -> User:
    """Seed and return a VENDOR user."""
    user = User(
        name="Vendor User",
        email="vendor@example.com",
        password_hash=hash_password("Vendor1234"),
        role=UserRole.VENDOR,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ── Auth helpers ──────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, admin_user: User) -> str:
    """Return a valid JWT access token for the admin user."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Admin1234"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["tokens"]["access_token"]


@pytest_asyncio.fixture
async def vendor_token(client: AsyncClient, vendor_user: User) -> str:
    """Return a valid JWT access token for the vendor user."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "vendor@example.com", "password": "Vendor1234"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["tokens"]["access_token"]


# ── Auth header helper ─────────────────────────────────────────────────────────

def auth_headers(token: str) -> dict:
    """Return an Authorization header dict for use in client requests."""
    return {"Authorization": f"Bearer {token}"}