"""
CloudBoard – Coverage Boost Tests (Modules 16 / 17 / 18).

Covers previously under-tested modules:
  - Organizations CRUD  (45% → target 60%+)
  - Search endpoint     (47% → target 60%+)
  - Auth dependencies   (63% → target 70%+)
  - System router       (65% → target 75%+)
  - Tasks router edges  (65% → target 75%+)

All tests run against the in-process ASGI app with SQLite via conftest.py fixtures.
"""

import os
import time
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_cloudboard.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("ENVIRONMENT", "development")

from app.main import app  # noqa: E402

client = TestClient(app)

# ── Unique suffix to prevent clashes across re-runs ──────────────────────────
_TS = str(int(time.time()))[-6:]
ORG_USER_EMAIL    = f"orgtest_{_TS}@cloudboard.dev"
ORG_USER_USERNAME = f"orguser_{_TS}"
ORG_USER_PASSWORD = "OrgTest#123"

# Module-level shared state (avoids class-level attr issues)
_STATE: dict = {
    "org_headers": {},
    "org_id": "",
    "search_headers": {},
}


# ═════════════════════════════════════════════════════════════════════════════
# Helper: register and return auth headers
# ═════════════════════════════════════════════════════════════════════════════

def _register_and_login(email: str, username: str, password: str = "OrgTest#123") -> dict:
    """Register (or login if already exists) and return auth header dict."""
    resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "username": username,
        "display_name": username.capitalize(),
        "password": password,
    })
    if resp.status_code == 409:
        resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code in (200, 201), f"Auth failed {resp.status_code}: {resp.text}"
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# ═════════════════════════════════════════════════════════════════════════════
# 1. Organizations  (ordered by number so pytest runs them sequentially)
# ═════════════════════════════════════════════════════════════════════════════

def test_org_01_setup_auth():
    """Register a user to use for org tests."""
    _STATE["org_headers"] = _register_and_login(ORG_USER_EMAIL, ORG_USER_USERNAME)


def test_org_02_create_organization():
    """POST /organizations/ → 201 with id and slug."""
    resp = client.post("/api/v1/organizations/", json={
        "name": f"Test Org {_TS}",
        "description": "Integration test org",
    }, headers=_STATE["org_headers"])
    assert resp.status_code == 201, f"Create org failed: {resp.text}"
    data = resp.json()
    assert "id" in data
    assert "slug" in data
    assert data["member_count"] == 1
    _STATE["org_id"] = data["id"]


def test_org_03_list_organizations_returns_created_org():
    """GET /organizations/ → includes newly created org."""
    resp = client.get("/api/v1/organizations/", headers=_STATE["org_headers"])
    assert resp.status_code == 200
    ids = [o["id"] for o in resp.json()]
    assert _STATE["org_id"] in ids


def test_org_04_get_organization_by_id():
    """GET /organizations/{id} → returns org details."""
    resp = client.get(
        f"/api/v1/organizations/{_STATE['org_id']}",
        headers=_STATE["org_headers"],
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == _STATE["org_id"]


def test_org_05_patch_organization():
    """PATCH /organizations/{id} → updates description."""
    resp = client.patch(
        f"/api/v1/organizations/{_STATE['org_id']}",
        json={"description": "Updated description"},
        headers=_STATE["org_headers"],
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == _STATE["org_id"]


def test_org_06_list_members():
    """GET /organizations/{id}/members → returns list."""
    resp = client.get(
        f"/api/v1/organizations/{_STATE['org_id']}/members",
        headers=_STATE["org_headers"],
    )
    assert resp.status_code == 200
    members = resp.json()
    assert isinstance(members, list)
    assert len(members) >= 1


def test_org_07_invite_member_invalid_role_rejected():
    """POST /organizations/{id}/invite with bad role → 400."""
    resp = client.post(
        f"/api/v1/organizations/{_STATE['org_id']}/invite",
        json={"email": "newmember@test.dev", "role": "superadmin"},
        headers=_STATE["org_headers"],
    )
    assert resp.status_code == 400


def test_org_08_invite_valid_member():
    """POST /organizations/{id}/invite with valid role → 201."""
    resp = client.post(
        f"/api/v1/organizations/{_STATE['org_id']}/invite",
        json={"email": f"invite_{_TS}@test.dev", "role": "developer"},
        headers=_STATE["org_headers"],
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "token" in data
    assert data["status"] == "pending"


def test_org_09_accept_invite_wrong_token():
    """POST /organizations/accept-invite with bogus token → 404."""
    resp = client.post(
        "/api/v1/organizations/accept-invite",
        json={"token": "not-a-valid-token-xyz"},
        headers=_STATE["org_headers"],
    )
    assert resp.status_code == 404


def test_org_10_get_org_requires_auth():
    """GET /organizations/{id} without auth → 401."""
    resp = client.get(f"/api/v1/organizations/{_STATE['org_id']}")
    assert resp.status_code == 401


def test_org_11_delete_organization():
    """DELETE /organizations/{id} → 200 with message."""
    resp = client.delete(
        f"/api/v1/organizations/{_STATE['org_id']}",
        headers=_STATE["org_headers"],
    )
    assert resp.status_code == 200
    assert "deleted" in resp.json()["message"].lower()


# ═════════════════════════════════════════════════════════════════════════════
# 2. Search
# ═════════════════════════════════════════════════════════════════════════════

def test_search_01_setup():
    """Register dedicated search-test user."""
    email    = f"search_{_TS}@cloudboard.dev"
    username = f"searchuser_{_TS}"
    _STATE["search_headers"] = _register_and_login(email, username)


def test_search_02_missing_query_returns_422():
    """GET /search without q param → 422."""
    resp = client.get("/api/v1/search", headers=_STATE["search_headers"])
    assert resp.status_code == 422


def test_search_03_tasks_scope():
    """GET /search?q=task&scope=task → 200 with SearchResponse shape."""
    resp = client.get("/api/v1/search?q=task&scope=task", headers=_STATE["search_headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert "query" in data
    assert "total" in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_search_04_all_scopes():
    """GET /search?q=test → 200 hitting all entity branches."""
    resp = client.get("/api/v1/search?q=test", headers=_STATE["search_headers"])
    assert resp.status_code == 200
    assert resp.json()["query"] == "test"


def test_search_05_organization_scope():
    """GET /search?q=org&scope=organization → 200."""
    resp = client.get("/api/v1/search?q=org&scope=organization", headers=_STATE["search_headers"])
    assert resp.status_code == 200


def test_search_06_member_scope():
    """GET /search?q=user&scope=member → 200."""
    resp = client.get("/api/v1/search?q=user&scope=member", headers=_STATE["search_headers"])
    assert resp.status_code == 200


def test_search_07_project_scope():
    """GET /search?q=proj&scope=project → 200."""
    resp = client.get("/api/v1/search?q=proj&scope=project", headers=_STATE["search_headers"])
    assert resp.status_code == 200


def test_search_08_requires_auth():
    """GET /search?q=anything without auth → 401."""
    resp = client.get("/api/v1/search?q=hello")
    assert resp.status_code == 401


def test_search_09_special_chars():
    """GET /search?q=test%25thing (percent escape) → 200, no crash."""
    resp = client.get("/api/v1/search?q=test%25thing", headers=_STATE["search_headers"])
    assert resp.status_code == 200


def test_search_10_pagination():
    """GET /search with limit and offset params → 200."""
    resp = client.get(
        "/api/v1/search?q=test&limit=5&offset=0",
        headers=_STATE["search_headers"],
    )
    assert resp.status_code == 200


# ═════════════════════════════════════════════════════════════════════════════
# 3. System / Observability Router
# ═════════════════════════════════════════════════════════════════════════════

def test_system_01_metrics():
    """GET /system/metrics → contains Prometheus-style metrics."""
    resp = client.get("/api/v1/system/metrics")
    assert resp.status_code == 200
    assert "cloudboard_uptime_seconds" in resp.text


def test_system_02_audit_logs_paginated():
    """GET /system/logs?page=1&limit=5 → paginated shape."""
    resp = client.get("/api/v1/system/logs?page=1&limit=5")
    assert resp.status_code == 200
    data = resp.json()
    items = data.get("items", data) if isinstance(data, dict) else data
    assert isinstance(items, list)


def test_system_03_audit_logs_large_page():
    """GET /system/logs?page=999 → 200, returns empty items gracefully."""
    resp = client.get("/api/v1/system/logs?page=999&limit=5")
    assert resp.status_code == 200


def test_system_04_health():
    """GET /health → healthy status."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_system_05_version():
    """GET /api/v1/version → returns version metadata."""
    resp = client.get("/api/v1/version")
    assert resp.status_code == 200
    data = resp.json()
    assert "version" in data
    assert "environment" in data


# ═════════════════════════════════════════════════════════════════════════════
# 4. Tasks Router Edge Cases
# ═════════════════════════════════════════════════════════════════════════════

def test_tasks_01_get_nonexistent():
    """GET /tasks/DOESNOTEXIST-999 → 404."""
    resp = client.get("/api/v1/tasks/DOESNOTEXIST-999")
    assert resp.status_code == 404


def test_tasks_02_update_nonexistent():
    """PUT /tasks/DOESNOTEXIST-999 → 404."""
    resp = client.put("/api/v1/tasks/DOESNOTEXIST-999", json={"status": "Doing"})
    assert resp.status_code == 404


def test_tasks_03_delete_nonexistent():
    """DELETE /tasks/DOESNOTEXIST-999 → 404."""
    resp = client.delete("/api/v1/tasks/DOESNOTEXIST-999")
    assert resp.status_code == 404


def test_tasks_04_create_minimal():
    """POST /tasks with minimal required fields → 201."""
    resp = client.post("/api/v1/tasks", json={
        "id": f"MIN-{_TS}",
        "title": "Minimal Task",
        "status": "Todo",
        "priority": "Low",
    })
    assert resp.status_code == 201
    assert resp.json()["id"] == f"MIN-{_TS}"


def test_tasks_05_create_full_fields():
    """POST /tasks with all optional fields → 201."""
    resp = client.post("/api/v1/tasks", json={
        "id": f"FULL-{_TS}",
        "title": "Full Task",
        "description": "All fields set",
        "status": "Doing",
        "priority": "High",
        "estimated_hours": 8,
        "actual_hours": 2,
        "labels": ["backend", "security"],
        "subtasks": [{"title": "Sub1", "done": False}],
        "comments": [],
    })
    assert resp.status_code == 201


def test_tasks_06_list_pagination():
    """GET /tasks?skip=0&limit=2 → list of at most 2 items."""
    resp = client.get("/api/v1/tasks?skip=0&limit=2")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) <= 2


def test_tasks_07_get_by_id():
    """GET /tasks/{id} for a task we just created → 200."""
    create = client.post("/api/v1/tasks", json={
        "id": f"GET-{_TS}",
        "title": "Get Me Task",
        "status": "Todo",
        "priority": "Medium",
    })
    assert create.status_code == 201
    resp = client.get(f"/api/v1/tasks/GET-{_TS}")
    assert resp.status_code == 200
    assert resp.json()["id"] == f"GET-{_TS}"


# ═════════════════════════════════════════════════════════════════════════════
# 5. Auth Dependency Paths
# ═════════════════════════════════════════════════════════════════════════════

def test_auth_dep_01_no_token_gives_401():
    """Any protected endpoint without any auth header → 401."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_auth_dep_02_malformed_bearer_gives_401():
    """Authorization header with garbage value → 401."""
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer garbage.token.here"})
    assert resp.status_code == 401


def test_auth_dep_03_wrong_scheme_gives_401():
    """Authorization: Basic ... instead of Bearer → 401."""
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert resp.status_code == 401


def test_auth_dep_04_valid_token_accesses_me():
    """Valid token grants access to /me."""
    email = f"dep_{_TS}@cloudboard.dev"
    username = f"dep_user_{_TS}"
    headers = _register_and_login(email, username)
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == email
