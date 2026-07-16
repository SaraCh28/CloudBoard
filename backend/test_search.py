"""
Module 6 – Search Service smoke test.
Tests the /api/v1/search endpoint for tasks, scoped results, and edge-cases.
"""

import sys
import httpx

BASE = "http://localhost:8000/api/v1"


def run():
    client = httpx.Client()

    # 1. Register + login to get a token
    print("── Auth setup ──────────────────────────────────────────")
    reg = client.post(f"{BASE}/auth/register", json={
        "email": "searchtest@example.com",
        "username": "searchtestuser",
        "display_name": "Search Tester",
        "password": "searchpassword123",
    })
    if reg.status_code == 409:
        login = client.post(f"{BASE}/auth/login", json={
            "email": "searchtest@example.com", "password": "searchpassword123"
        })
        token = login.json()["access_token"]
    else:
        assert reg.status_code == 201, f"Register failed: {reg.text}"
        token = reg.json()["access_token"]
    print(f"Token acquired. User: searchtest@example.com")

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create a task to search
    print("\n── Creating a task ──────────────────────────────────────")
    client.post(f"{BASE}/tasks", json={
        "id": "SRCH-001",
        "title": "Implement global search indexing",
        "description": "Add PostgreSQL tsvector support",
        "status": "Todo",
        "priority": "High",
        "estimated_hours": 12,
        "actual_hours": 0,
        "labels": ["search", "backend"],
        "subtasks": [],
        "comments": [],
    })
    print("Task SRCH-001 seeded.")

    # 3. Search for the task
    print("\n── Test 1: Task search for 'global search' ─────────────")
    res = client.get(f"{BASE}/search?q=global+search", headers=headers)
    assert res.status_code == 200, f"Search failed: {res.text}"
    data = res.json()
    print(f"  Total results: {data['total']}")
    print(f"  First 3 hits:")
    for hit in data["results"][:3]:
        print(f"    [{hit['type']}] {hit['title']} — {hit['subtitle']}")

    task_hits = [h for h in data["results"] if h["type"] == "task"]
    assert len(task_hits) > 0, "Expected at least one task result for 'global search'"
    print("  ✓ Task found in results")

    # 4. Scoped search — only tasks
    print("\n── Test 2: Scoped task-only search ─────────────────────")
    res = client.get(f"{BASE}/search?q=search&scope=task", headers=headers)
    assert res.status_code == 200
    data = res.json()
    types = {h["type"] for h in data["results"]}
    assert types.issubset({"task"}), f"Expected only task hits, got: {types}"
    print(f"  ✓ Scope=task enforced. {data['total']} task result(s)")

    # 5. Empty query protection
    print("\n── Test 3: Empty query (should reject) ─────────────────")
    res = client.get(f"{BASE}/search?q=", headers=headers)
    assert res.status_code == 422, f"Expected 422, got {res.status_code}"
    print("  ✓ Empty query returns 422")

    # 6. Unauthenticated search (should reject)
    print("\n── Test 4: Unauthenticated search (should reject) ──────")
    res = client.get(f"{BASE}/search?q=task")
    assert res.status_code == 401, f"Expected 401, got {res.status_code}"
    print("  ✓ Unauthenticated request returns 401")

    print("\n✅ All Module 6 Search Service tests passed!")


if __name__ == "__main__":
    run()
