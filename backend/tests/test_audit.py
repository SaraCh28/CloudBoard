"""
CloudBoard – AuditService Unit Tests (Module 16 / 17).

Uses an in-memory SQLite engine to test AuditLog write/read operations
without hitting the main test DB.
"""

import asyncio
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.database import Base
from app.models.audit_log import AuditLog
from app.services.audit import audit


# ── In-memory engine for isolation ───────────────────────────────
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def db_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session

    await engine.dispose()


# ── Tests ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_audit_log_write_success(db_session):
    """AuditService.log() persists an entry with correct fields."""
    entry = await audit.log(
        db_session,
        action="login",
        status="success",
        user_id="user-abc-123",
        username="testuser",
        resource_type="user",
        resource_id="user-abc-123",
        detail="Test login event",
    )
    await db_session.commit()

    assert entry.id is not None
    assert entry.action == "login"
    assert entry.status == "success"
    assert entry.user_id == "user-abc-123"
    assert entry.username == "testuser"
    assert entry.timestamp is not None


@pytest.mark.asyncio
async def test_audit_log_failure_entry(db_session):
    """AuditService writes failure entries correctly."""
    entry = await audit.log(
        db_session,
        action="login",
        status="failure",
        detail="Invalid credentials for unknown@test.dev",
    )
    await db_session.commit()

    assert entry.status == "failure"
    assert entry.user_id is None  # anonymous
    assert "Invalid credentials" in entry.detail


@pytest.mark.asyncio
async def test_audit_log_to_dict(db_session):
    """to_dict() returns all expected keys with correct types."""
    entry = await audit.log(
        db_session,
        action="change_password",
        status="success",
        user_id="user-xyz",
        username="pwdchanger",
    )
    await db_session.commit()

    d = entry.to_dict()
    assert isinstance(d, dict)
    for key in ("id", "user_id", "username", "action", "status", "timestamp"):
        assert key in d
    assert d["action"] == "change_password"
    assert isinstance(d["timestamp"], str)


@pytest.mark.asyncio
async def test_multiple_audit_entries_preserved(db_session):
    """Multiple entries for the same user are all stored independently."""
    for action in ("register", "login", "logout"):
        await audit.log(
            db_session,
            action=action,
            user_id="multi-user",
            username="multitest",
        )
    await db_session.commit()

    from sqlalchemy import select
    result = await db_session.execute(
        select(AuditLog).where(AuditLog.user_id == "multi-user")
    )
    rows = result.scalars().all()
    assert len(rows) >= 3
    found_actions = {r.action for r in rows}
    assert {"register", "login", "logout"}.issubset(found_actions)
