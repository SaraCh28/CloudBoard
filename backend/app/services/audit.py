"""
CloudBoard – Audit Service (Module 16).

Provides a thin async interface for writing structured audit entries
to the `audit_logs` table. Call `audit.log()` from any router that
performs a security-relevant action.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditService:
    """Write-only service for recording audit trail entries."""

    @staticmethod
    async def log(
        db: AsyncSession,
        *,
        action: str,
        status: str = "success",
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        detail: Optional[str] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """
        Persist an audit log entry.

        Parameters
        ----------
        db            Active async DB session (caller must commit).
        action        Short action code, e.g. "login", "register", "logout",
                      "change_password", "file_upload", "task_delete".
        status        "success" or "failure".
        user_id       UUID string of the acting user (None for anonymous).
        username      Display username for quick read without JOIN.
        resource_type Entity class that was affected, e.g. "user", "task".
        resource_id   ID of the affected entity.
        detail        Human-readable summary (e.g. error message on failure).
        request       FastAPI request for extracting IP + User-Agent.
        """
        ip: Optional[str] = None
        ua: Optional[str] = None

        if request is not None:
            # X-Forwarded-For takes precedence (reverse-proxy setups)
            forwarded = request.headers.get("x-forwarded-for")
            ip = forwarded.split(",")[0].strip() if forwarded else (
                request.client.host if request.client else None
            )
            ua = request.headers.get("user-agent")

        entry = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            detail=detail,
            ip_address=ip,
            user_agent=ua,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(entry)
        # Flush so the ID is populated; caller is responsible for commit.
        await db.flush()
        return entry


# Singleton – import this in routers
audit = AuditService()
