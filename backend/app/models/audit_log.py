"""
CloudBoard – AuditLog Model (Module 16).

Records every security-relevant action (login, logout, register,
password change, file upload) with actor identity, IP, and user-agent.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    # Actor (nullable for unauthenticated actions like failed login)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # What happened
    action: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. "login", "register"
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)   # "user", "task", "file"
    resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Outcome
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="success")  # "success" | "failure"
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Request context
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)   # IPv4 or IPv6
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    __table_args__ = (
        # Composite index for most common admin query: filter by user, order by time
        Index("ix_audit_logs_user_id_timestamp", "user_id", "timestamp"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "status": self.status,
            "detail": self.detail,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
