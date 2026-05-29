"""
Test configuration and fixtures for the VeriCred Share backend test suite.
"""

import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base, get_db
from app.main import app

# ── Test Database (SQLite in-memory for speed) ───────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create and drop tables for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Direct database session for test setup/assertions."""
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """Register a test user and return auth headers."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"test-{uuid.uuid4().hex[:8]}@example.com",
            "full_name": "Test User",
            "password": "SecurePass123",
        },
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_credential(client: AsyncClient, auth_headers: dict) -> dict:
    """Issue a test credential and return its data."""
    response = await client.post(
        "/api/v1/credentials/issue",
        json={
            "credential_type": "AcademicCredential",
            "claims": {
                "name": "Test Student",
                "degree": "B.Tech Computer Science",
                "university": "IIT Delhi",
                "graduationYear": 2025,
                "cgpa": 8.5,
                "rollNumber": "CS2021001",
                "issuerName": "Academic Records Office",
            },
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()
