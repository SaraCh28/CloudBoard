# ADR 003 – SQLite for Test Environment

**Date**: 2026-07-26  
**Status**: Accepted

---

## Context

Backend tests need a database. Running a full PostgreSQL instance in every developer machine and CI runner adds complexity and startup time.

## Decision

Use **SQLite + aiosqlite** as the test database, injected before app startup:

```python
# tests/conftest.py
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_cloudboard.db"
```

SQLAlchemy 2.0 with `asyncpg` (production) and `aiosqlite` (test) share the same ORM layer. The dialect difference is transparent to model code.

## Trade-offs

| | SQLite (test) | PostgreSQL (production) |
|-|---------------|-------------------------|
| Setup | Zero — file-based | Requires server |
| Speed | Very fast | Slower startup |
| Full-text search | Limited | `tsvector` / GIN indexes |
| JSON operators | Limited | Native `jsonb` |
| Migrations | Not tested | Fully tested |

## Mitigations

- Integration tests that specifically exercise PostgreSQL features (GIN FTS search) are marked `@pytest.mark.slow` and run in CI against a real Postgres service.
- Alembic migration tests always target PostgreSQL (separate CI job).

## Consequences

✅ Zero-dependency test suite — runs `pytest` immediately after `pip install`  
⚠️ PostgreSQL-specific features are not validated in unit/integration tests
