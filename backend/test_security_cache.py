"""
Unit tests for CloudBoard Security Hardening, Rate Limiting, and Cache Service (Modules 13 & 16).
"""

from fastapi.testclient import TestClient
from app.main import app
from app.services.cache import cache_service
from app.middleware.security import sanitize_input

client = TestClient(app)


def test_security_headers():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-xss-protection") == "1; mode=block"


def test_rate_limit_headers():
    response = client.get("/api/v1/system/logs")
    assert response.status_code == 200
    assert "x-ratelimit-limit" in response.headers
    assert "x-ratelimit-remaining" in response.headers


def test_cache_service():
    cache_service.set("test_key", {"status": "ok"}, ttl=10)
    cached = cache_service.get("test_key")
    assert cached is not None
    assert cached["status"] == "ok"
    
    stats = cache_service.get_stats()
    assert stats["hits"] >= 1
    assert stats["total_keys"] >= 1


def test_input_sanitizer():
    dirty = "<script>alert('xss')</script> Hello World & Test"
    clean = sanitize_input(dirty)
    assert "<script>" not in clean
    assert "&amp;" in clean
