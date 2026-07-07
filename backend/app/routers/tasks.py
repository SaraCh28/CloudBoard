"""
CloudBoard – Tasks Router.

Endpoints: list, create, update, delete.
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.task import Task

# We are intentionally leaving out get_current_user here to allow the 
# prototype frontend to work without a full login screen for now.
# In a real production app, all these endpoints would require `Depends(get_current_user)`.

router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])


# ── Schemas ──────────────────────────────────────────────────────
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1)
    description: str | None = None
    status: str = "Todo"
    priority: str = "Medium"
    estimated_hours: int = 8
    actual_hours: int = 0
    labels: list[str] = []
    subtasks: list[dict[str, Any]] = []
    comments: list[dict[str, Any]] = []
    assigneeId: str | None = None  # Frontend sends camelCase sometimes


class TaskCreate(TaskBase):
    id: str  # Frontend generates IDs like "PHX-101" for now


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    estimated_hours: int | None = None
    actual_hours: int | None = None
    labels: list[str] | None = None
    subtasks: list[dict[str, Any]] | None = None
    comments: list[dict[str, Any]] | None = None
    assigneeId: str | None = None


class TaskResponse(TaskBase):
    id: str
    
    class Config:
        from_attributes = True
        populate_by_name = True


# ── Routes ───────────────────────────────────────────────────────
@router.get("", response_model=list[TaskResponse])
async def list_tasks(db: AsyncSession = Depends(get_db)):
    """Get all tasks."""
    result = await db.execute(select(Task).order_by(Task.created_at.desc()))
    tasks = result.scalars().all()
    # map assignee_id to assigneeId for frontend
    out = []
    for t in tasks:
        out.append({
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "status": t.status,
            "priority": t.priority,
            "estimated_hours": t.estimated_hours,
            "actual_hours": t.actual_hours,
            "labels": t.labels,
            "subtasks": t.subtasks,
            "comments": t.comments,
            "assigneeId": t.assignee_id
        })
    return out


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(body: TaskCreate, db: AsyncSession = Depends(get_db)):
    """Create a new task."""
    task = Task(
        id=body.id,
        title=body.title,
        description=body.description,
        status=body.status,
        priority=body.priority,
        estimated_hours=body.estimated_hours,
        actual_hours=body.actual_hours,
        labels=body.labels,
        subtasks=body.subtasks,
        comments=body.comments,
        assignee_id=body.assigneeId
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    res = {**body.dict(), "assigneeId": task.assignee_id}
    return res


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, body: TaskUpdate, db: AsyncSession = Depends(get_db)):
    """Update a task."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = body.dict(exclude_unset=True)
    
    # Handle mapping assigneeId to assignee_id
    if "assigneeId" in update_data:
        task.assignee_id = update_data.pop("assigneeId")
        
    for key, value in update_data.items():
        setattr(task, key, value)

    await db.commit()
    await db.refresh(task)
    
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "estimated_hours": task.estimated_hours,
        "actual_hours": task.actual_hours,
        "labels": task.labels,
        "subtasks": task.subtasks,
        "comments": task.comments,
        "assigneeId": task.assignee_id
    }


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a task."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await db.delete(task)
    await db.commit()
