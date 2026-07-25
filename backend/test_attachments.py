"""
Tests for CloudBoard File Attachment Service.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_upload_and_list_attachment():
    file_content = b"CloudBoard architecture document content"
    files = {"file": ("test_arch.txt", file_content, "text/plain")}
    data = {"task_id": "PHX-101"}

    response = client.post("/api/v1/attachments/upload", data=data, files=files)
    assert response.status_code == 201
    attachment = response.json()
    assert attachment["task_id"] == "PHX-101"
    assert attachment["original_name"] == "test_arch.txt"
    assert attachment["url"].startswith("/uploads/")

    # List attachments
    list_res = client.get("/api/v1/attachments/PHX-101")
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) >= 1
    assert items[0]["id"] == attachment["id"]

    # Delete attachment
    del_res = client.delete(f"/api/v1/attachments/{attachment['id']}")
    assert del_res.status_code == 200


def test_upload_invalid_extension():
    files = {"file": ("malicious.exe", b"binary", "application/octet-stream")}
    data = {"task_id": "PHX-102"}

    response = client.post("/api/v1/attachments/upload", data=data, files=files)
    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]
