"""
CloudBoard – Search Router (Module 6).

Provides global full-text and prefix search across:
  - Tasks        (title, description)
  - Projects     (name, description)
  - Organizations (name, slug, description)  [scoped to user membership]
  - Members      (username, display_name, email) [scoped to shared orgs]

Strategy:
  - PostgreSQL ILIKE for broad compatibility (no tsvector migration needed yet).
  - Each result carries a `type` discriminator so the frontend can route to the
    correct view.
  - Pagination: `limit` (max 50) + `offset`.
  - Optional `scope` query param to narrow to a single entity type.
"""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.organization import Organization, OrganizationMember
from app.models.project import Project
from app.models.task import Task

router = APIRouter(prefix="/api/v1/search", tags=["Search"])

# ── Response Shapes ──────────────────────────────────────────────────────────
from pydantic import BaseModel
from datetime import datetime


class SearchHit(BaseModel):
    """A single search result."""
    type: Literal["task", "project", "organization", "member"]
    id: str
    title: str
    subtitle: str | None = None
    url_hint: str  # e.g. "/kanban?task=PHX-101" — front-end uses this for routing
    score_hint: int = 0  # simple ranking: title match = 2, description/other = 1


class SearchResponse(BaseModel):
    query: str
    total: int
    results: list[SearchHit]


# ── Helper ────────────────────────────────────────────────────────────────────
def _ilike(q: str) -> str:
    """Wrap query in ILIKE wildcard pattern."""
    safe = q.replace("%", r"\%").replace("_", r"\_")
    return f"%{safe}%"


# ── Endpoint ──────────────────────────────────────────────────────────────────
@router.get("", response_model=SearchResponse)
async def global_search(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    scope: str | None = Query(
        None,
        description="Narrow search: task | project | organization | member",
    ),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Global full-text search across tasks, projects, organizations, and members."""
    pattern = _ilike(q)
    hits: list[SearchHit] = []

    # ── Resolve user's org membership once ───────────────────────────────────
    org_ids_result = await db.execute(
        select(OrganizationMember.organization_id).where(
            OrganizationMember.user_id == current_user.id
        )
    )
    user_org_ids = [row[0] for row in org_ids_result.all()]

    # ── Tasks ─────────────────────────────────────────────────────────────────
    if scope in (None, "task"):
        task_result = await db.execute(
            select(Task).where(
                or_(
                    Task.title.ilike(pattern),
                    Task.description.ilike(pattern),
                )
            ).order_by(Task.created_at.desc()).limit(limit).offset(offset)
        )
        for task in task_result.scalars().all():
            title_match = q.lower() in (task.title or "").lower()
            hits.append(SearchHit(
                type="task",
                id=str(task.id),
                title=task.title,
                subtitle=f"{task.status} · {task.priority}",
                url_hint=f"/kanban?task={task.id}",
                score_hint=2 if title_match else 1,
            ))

    # ── Projects ──────────────────────────────────────────────────────────────
    if scope in (None, "project"):
        if user_org_ids:
            proj_result = await db.execute(
                select(Project).where(
                    Project.organization_id.in_(user_org_ids),
                    or_(
                        Project.name.ilike(pattern),
                        Project.description.ilike(pattern),
                    ),
                ).order_by(Project.created_at.desc()).limit(limit).offset(offset)
            )
            for project in proj_result.scalars().all():
                title_match = q.lower() in (project.name or "").lower()
                hits.append(SearchHit(
                    type="project",
                    id=str(project.id),
                    title=project.name,
                    subtitle=project.key,
                    url_hint=f"/projects/{project.id}",
                    score_hint=2 if title_match else 1,
                ))

    # ── Organizations ─────────────────────────────────────────────────────────
    if scope in (None, "organization"):
        if user_org_ids:
            org_result = await db.execute(
                select(Organization).where(
                    Organization.id.in_(user_org_ids),
                    or_(
                        Organization.name.ilike(pattern),
                        Organization.slug.ilike(pattern),
                        Organization.description.ilike(pattern),
                    ),
                ).limit(limit).offset(offset)
            )
            for org in org_result.scalars().all():
                title_match = q.lower() in (org.name or "").lower()
                hits.append(SearchHit(
                    type="organization",
                    id=str(org.id),
                    title=org.name,
                    subtitle=org.slug,
                    url_hint=f"/orgs/{org.id}",
                    score_hint=2 if title_match else 1,
                ))

    # ── Members ───────────────────────────────────────────────────────────────
    if scope in (None, "member"):
        if user_org_ids:
            member_result = await db.execute(
                select(User).join(
                    OrganizationMember, OrganizationMember.user_id == User.id
                ).where(
                    OrganizationMember.organization_id.in_(user_org_ids),
                    or_(
                        User.username.ilike(pattern),
                        User.display_name.ilike(pattern),
                        User.email.ilike(pattern),
                    ),
                ).distinct().limit(limit).offset(offset)
            )
            for user in member_result.scalars().all():
                title_match = q.lower() in (user.display_name or "").lower()
                hits.append(SearchHit(
                    type="member",
                    id=str(user.id),
                    title=user.display_name,
                    subtitle=user.email,
                    url_hint=f"/members/{user.id}",
                    score_hint=2 if title_match else 1,
                ))

    # ── Sort by score descending, then stable by type ─────────────────────────
    hits.sort(key=lambda h: -h.score_hint)

    return SearchResponse(query=q, total=len(hits), results=hits)
