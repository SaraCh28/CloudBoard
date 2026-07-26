"""
CloudBoard – File Attachment & Storage Router (Module 9).
Provides file upload, storage, listing, and validation for task assets.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, status, Form
from typing import List, Optional, Dict
import os
import uuid
import time
import shutil
from pydantic import BaseModel
from app.middleware.security import validate_file_upload

router = APIRouter(prefix="/api/v1/attachments", tags=["File Attachments"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf", ".txt", ".md", ".json", ".csv", ".zip"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB limit

# In-memory attachment metadata store (production uses S3/DB)
attachment_db: Dict[str, List[dict]] = {}


class AttachmentResponse(BaseModel):
    id: str
    task_id: str
    filename: str
    original_name: str
    content_type: str
    size_bytes: int
    url: str
    uploaded_at: float


@router.post("/upload", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    task_id: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload a file attachment for a specific task."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext}' is not allowed. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read content first to get size
    content = await file.read()
    size_bytes = len(content)

    # Module 16: Validate MIME type, extension, and size
    ok, reason = validate_file_upload(
        filename=file.filename,
        content_type=file.content_type,
        size_bytes=size_bytes,
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)

    attachment_id = f"att-{uuid.uuid4().hex[:8]}"
    safe_filename = f"{attachment_id}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(content)

    attachment = {
        "id": attachment_id,
        "task_id": task_id,
        "filename": safe_filename,
        "original_name": file.filename,
        "content_type": file.content_type or "application/octet-stream",
        "size_bytes": size_bytes,
        "url": f"/uploads/{safe_filename}",
        "uploaded_at": time.time()
    }

    if task_id not in attachment_db:
        attachment_db[task_id] = []
    attachment_db[task_id].append(attachment)

    return attachment


@router.get("/{task_id}", response_model=List[AttachmentResponse])
async def list_task_attachments(task_id: str):
    """Retrieve all file attachments uploaded for a task."""
    return attachment_db.get(task_id, [])


@router.delete("/{attachment_id}")
async def delete_attachment(attachment_id: str):
    """Delete an attachment by ID."""
    found = False
    for task_id, att_list in attachment_db.items():
        for att in list(att_list):
            if att["id"] == attachment_id:
                file_path = os.path.join(UPLOAD_DIR, att["filename"])
                if os.path.exists(file_path):
                    os.remove(file_path)
                att_list.remove(att)
                found = True
                break
        if found:
            break
    
    if not found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    
    return {"message": "Attachment deleted successfully", "id": attachment_id}
