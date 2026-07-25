"""
Tests for CloudBoard System Admin & Observability Endpoints.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "CloudBoard"


def test_detailed_system_health():
    response = client.get("/api/v1/system/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "system_resources" in data


def test_prometheus_metrics():
    response = client.get("/api/v1/system/metrics")
    assert response.status_code == 200
    assert "cloudboard_uptime_seconds" in response.text
    assert "cloudboard_requests_total" in response.text


def test_system_logs():
    response = client.get("/api/v1/system/logs")
    assert response.status_code == 200
    logs = response.json()
    assert isinstance(logs, list)
    assert len(logs) > 0
    assert "service" in logs[0]
