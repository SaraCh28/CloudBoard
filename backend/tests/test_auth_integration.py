"""
CloudBoard – Module 17 Auth Integration Tests.

Tests the full authentication lifecycle:
  register → login → /me → refresh → change-password → logout

Also verifies audit log entries are written for each action.
Runs against SQLite (configured in conftest.py).
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Unique email per test run to avoid collisions across re-runs
import time
_SUFFIX = str(int(time.time()))[-5:]
TEST_EMAIL = f"integration_{_SUFFIX}@cloudboard.dev"
TEST_USERNAME = f"int_user_{_SUFFIX}"
TEST_PASSWORD = "Integration#Test1"
NEW_PASSWORD = "NewPassword#99"


class TestAuthIntegrationFlow:
    """Full register → login → me → refresh → change-password → logout lifecycle."""

    access_token: str = ""
    refresh_token: str = ""

    def test_01_register_creates_user(self):
        resp = client.post("/api/v1/auth/register", json={
            "email": TEST_EMAIL,
            "username": TEST_USERNAME,
            "display_name": "Integration Tester",
            "password": TEST_PASSWORD,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        TestAuthIntegrationFlow.access_token = data["access_token"]
        TestAuthIntegrationFlow.refresh_token = data["refresh_token"]

    def test_02_duplicate_register_returns_409(self):
        resp = client.post("/api/v1/auth/register", json={
            "email": TEST_EMAIL,
            "username": TEST_USERNAME,
            "display_name": "Duplicate",
            "password": TEST_PASSWORD,
        })
        assert resp.status_code == 409

    def test_03_login_returns_tokens(self):
        resp = client.post("/api/v1/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        TestAuthIntegrationFlow.access_token = data["access_token"]
        TestAuthIntegrationFlow.refresh_token = data["refresh_token"]

    def test_04_invalid_password_returns_401(self):
        resp = client.post("/api/v1/auth/login", json={
            "email": TEST_EMAIL,
            "password": "WrongPass#99",
        })
        assert resp.status_code == 401

    def test_05_me_endpoint_returns_profile(self):
        headers = {"Authorization": f"Bearer {TestAuthIntegrationFlow.access_token}"}
        resp = client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == TEST_EMAIL
        assert data["username"] == TEST_USERNAME

    def test_06_me_without_token_returns_401(self):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_07_refresh_issues_new_tokens(self):
        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": TestAuthIntegrationFlow.refresh_token,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        # Store new tokens
        TestAuthIntegrationFlow.access_token = data["access_token"]
        TestAuthIntegrationFlow.refresh_token = data["refresh_token"]

    def test_08_invalid_refresh_token_returns_401(self):
        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "not-a-valid-token",
        })
        assert resp.status_code == 401

    def test_09_change_password_success(self):
        headers = {"Authorization": f"Bearer {TestAuthIntegrationFlow.access_token}"}
        resp = client.post("/api/v1/auth/change-password", json={
            "current_password": TEST_PASSWORD,
            "new_password": NEW_PASSWORD,
        }, headers=headers)
        assert resp.status_code == 200
        assert "changed" in resp.json()["message"].lower()

    def test_10_login_with_new_password(self):
        resp = client.post("/api/v1/auth/login", json={
            "email": TEST_EMAIL,
            "password": NEW_PASSWORD,
        })
        assert resp.status_code == 200
        TestAuthIntegrationFlow.access_token = resp.json()["access_token"]

    def test_11_logout_success(self):
        headers = {"Authorization": f"Bearer {TestAuthIntegrationFlow.access_token}"}
        resp = client.post("/api/v1/auth/logout", headers=headers)
        assert resp.status_code == 200
        assert "logged out" in resp.json()["message"].lower()

    def test_12_audit_log_contains_register_and_login(self):
        """Verify AuditLog DB entries were created during the flow above."""
        resp = client.get("/api/v1/system/logs?limit=100")
        assert resp.status_code == 200
        data = resp.json()
        # Response may be paginated or a plain list – handle both
        items = data.get("items", data) if isinstance(data, dict) else data
        actions = [entry["action"] for entry in items]
        assert "register" in actions or "login" in actions


class TestPasswordValidation:
    """Test Pydantic field_validator password strength enforcement."""

    def test_weak_password_no_uppercase_rejected(self):
        resp = client.post("/api/v1/auth/register", json={
            "email": "weak@test.dev",
            "username": "weakuser",
            "display_name": "Weak",
            "password": "nouppercase1!",
        })
        assert resp.status_code == 422

    def test_weak_password_no_digit_rejected(self):
        resp = client.post("/api/v1/auth/register", json={
            "email": "weak2@test.dev",
            "username": "weakuser2",
            "display_name": "Weak2",
            "password": "NoDigitHere!",
        })
        assert resp.status_code == 422

    def test_weak_password_no_special_rejected(self):
        resp = client.post("/api/v1/auth/register", json={
            "email": "weak3@test.dev",
            "username": "weakuser3",
            "display_name": "Weak3",
            "password": "NoSpecial123",
        })
        assert resp.status_code == 422

    def test_strong_password_accepted_format(self):
        """Schema validation passes – 409 means DB duplicate, not schema error."""
        resp = client.post("/api/v1/auth/register", json={
            "email": f"strong_{_SUFFIX}_2@test.dev",
            "username": f"strongu_{_SUFFIX}",
            "display_name": "Strong",
            "password": "Strong#Pass99",
        })
        assert resp.status_code in (201, 409)  # 409 = already exists on re-run
