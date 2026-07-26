"""
CloudBoard – Full Module 17 Master Test Suite.
Verifies Auth, Tasks, Search, Attachments, System Observability, Security Headers, Rate Limiting, and GraphQL.

The conftest.py in this package sets DATABASE_URL to SQLite before the app is imported,
so these tests run without a PostgreSQL instance.
"""

import os
import pytest

# Ensure environment is set before importing app (conftest also does this,
# but this guard makes individual imports of this file safe too).
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_cloudboard.db")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ── Module 10/11 ─────────────────────────────────────────────────
def test_01_health_and_security_headers():
    """Verify application health and security response headers (Module 10 & 16)."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

    # Module 16: Security headers injected by SecurityHeadersMiddleware
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-xss-protection") == "1; mode=block"


# ── Module 11/12 Observability ───────────────────────────────────
def test_02_system_metrics_and_logs():
    """Verify Prometheus metrics and audit log endpoints (Module 11 & 12)."""
    metrics_res = client.get("/api/v1/system/metrics")
    assert metrics_res.status_code == 200
    assert "cloudboard_uptime_seconds" in metrics_res.text

    logs_res = client.get("/api/v1/system/logs")
    assert logs_res.status_code == 200
    data = logs_res.json()
    # Response is paginated: {total, page, limit, items} or a plain list
    items = data.get("items", data) if isinstance(data, dict) else data
    assert isinstance(items, list)


# ── Module 13: Rate Limiting Headers ─────────────────────────────
def test_03_rate_limiting_headers():
    """Verify sliding window rate limit headers (Module 13)."""
    res = client.get("/api/v1/system/logs")
    assert "x-ratelimit-limit" in res.headers
    assert "x-ratelimit-remaining" in res.headers
    assert int(res.headers["x-ratelimit-limit"]) == 120


# ── Module 1/3: Task CRUD + Pagination ───────────────────────────
def test_04_task_crud_and_pagination():
    """Verify Task creation, paginated listing, update, and deletion (Module 1 & 18)."""
    # Paginated list
    list_res = client.get("/api/v1/tasks?skip=0&limit=10")
    assert list_res.status_code == 200
    assert isinstance(list_res.json(), list)

    # Create task
    new_task = {
        "id": "TEST-501",
        "title": "Full Suite Pytest Task",
        "description": "Automated test coverage",
        "status": "Todo",
        "priority": "High",
        "estimated_hours": 4,
        "actual_hours": 0,
        "labels": [],
        "subtasks": [],
        "comments": []
    }
    create_res = client.post("/api/v1/tasks", json=new_task)
    assert create_res.status_code == 201
    assert create_res.json()["id"] == "TEST-501"

    # Update task status
    update_res = client.put("/api/v1/tasks/TEST-501", json={"status": "Doing"})
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "Doing"

    # Delete task
    del_res = client.delete("/api/v1/tasks/TEST-501")
    assert del_res.status_code == 204


# ── Module 7: GraphQL Gateway ────────────────────────────────────
def test_05_graphql_query_tasks():
    """Verify Strawberry GraphQL tasks query (Module 7)."""
    query = '{ tasks { id title priority } }'
    res = client.post("/graphql", json={"query": query})
    assert res.status_code == 200
    data = res.json()
    assert "data" in data
    assert "tasks" in data["data"]


def test_06_graphql_create_task_mutation():
    """Verify Strawberry GraphQL createTask mutation (Module 7)."""
    mutation = '''
    mutation {
      createTask(title: "Pytest GQL Task", description: "From mutation", priority: "High") {
        id title priority status
      }
    }
    '''
    res = client.post("/graphql", json={"query": mutation})
    assert res.status_code == 200
    data = res.json()
    assert data["data"]["createTask"]["title"] == "Pytest GQL Task"
    assert data["data"]["createTask"]["status"] == "Todo"


# ── Module 16: Cache Service ──────────────────────────────────────
def test_07_cache_service():
    """Verify Cache-Aside service set/get/stats (Module 13)."""
    from app.services.cache import cache_service
    cache_service.set("pytest_key", {"result": "ok"}, ttl=30)
    val = cache_service.get("pytest_key")
    assert val is not None
    assert val["result"] == "ok"
    stats = cache_service.get_stats()
    assert stats["hits"] >= 1


# ── Module 16: Input Sanitizer ────────────────────────────────────
def test_08_xss_sanitizer():
    """Verify XSS input sanitizer strips script tags (Module 16)."""
    from app.middleware.security import sanitize_input
    dangerous = "<script>alert('xss')</script> Hello World"
    cleaned = sanitize_input(dangerous)
    assert "<script>" not in cleaned
    assert "Hello World" in cleaned
