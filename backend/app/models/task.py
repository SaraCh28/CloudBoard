"""
CloudBoard – Task ORM model.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import String, Integer, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # Frontend uses e.g. "PHX-101"
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="Todo")
    priority: Mapped[str] = mapped_column(String(32), default="Medium")
    
    estimated_hours: Mapped[int] = mapped_column(Integer, default=8)
    actual_hours: Mapped[int] = mapped_column(Integer, default=0)
    
    # Store frontend labels, subtasks, and comments as JSON
    labels: Mapped[list[str]] = mapped_column(JSON, default=list)
    subtasks: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    comments: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)

    assignee_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Task {self.id}: {self.title}>"
