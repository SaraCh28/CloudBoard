"""
Pytest conftest – CloudBoard test suite.

Patches DATABASE_URL to SQLite (aiosqlite) before any app import so
tests run without a running PostgreSQL instance.

Provides:
  client       – synchronous TestClient (fast, most tests)
  async_client – async httpx.AsyncClient (for async integration tests)
  db_session   – isolated async DB session per test
"""

import os
import asyncio
import pytest
import pytest_asyncio

# ── Must be set BEFORE any app import (settings are @lru_cache'd) ─
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_cloudboard.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("ENVIRONMENT", "development")

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import engine, Base, get_db
import app.models  # noqa: F401 – ensures all models are registered


# ── Create tables once per session ───────────────────────────────
def pytest_configure(config):
    """Create all DB tables before any tests run."""
    async def _create():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(_create())


# ── Synchronous TestClient ────────────────────────────────────────
@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


# ── Async Client fixture ──────────────────────────────────────────
@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ── Registered test user helper ───────────────────────────────────
@pytest.fixture(scope="session")
def registered_user(client):
    """Register a test user and return credentials + tokens."""
    payload = {
        "email": "pytest@cloudboard.dev",
        "username": "pytestuser",
        "display_name": "Pytest User",
        "password": "Secure#123",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    # If already exists (re-run), login instead
    if resp.status_code == 409:
        resp = client.post("/api/v1/auth/login", json={
            "email": payload["email"],
            "password": payload["password"],
        })
    assert resp.status_code in (200, 201)
    tokens = resp.json()
    return {"credentials": payload, "tokens": tokens}


@pytest.fixture(scope="session")
def auth_headers(registered_user):
    """Return Authorization header dict for authenticated requests."""
    return {"Authorization": f"Bearer {registered_user['tokens']['access_token']}"}
