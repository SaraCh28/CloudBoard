"""
CloudBoard – Role-Based Access Control helpers.

Provides a FastAPI dependency factory that checks organization-level permissions.
"""

from functools import wraps
from typing import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.organization import OrganizationMember, OrgRole

# Permission matrix: which roles can perform which actions
PERMISSION_MATRIX: dict[str, set[OrgRole]] = {
    "create_project":   {OrgRole.OWNER, OrgRole.ADMIN, OrgRole.MANAGER},
    "delete_project":   {OrgRole.OWNER, OrgRole.ADMIN},
    "edit_task":        {OrgRole.OWNER, OrgRole.ADMIN, OrgRole.MANAGER, OrgRole.DEVELOPER},
    "manage_users":     {OrgRole.OWNER, OrgRole.ADMIN},
    "view_analytics":   {OrgRole.OWNER, OrgRole.ADMIN, OrgRole.MANAGER},
    "manage_billing":   {OrgRole.OWNER},
    "delete_org":       {OrgRole.OWNER},
    "invite_member":    {OrgRole.OWNER, OrgRole.ADMIN, OrgRole.MANAGER},
    "remove_member":    {OrgRole.OWNER, OrgRole.ADMIN},
    "transfer_ownership": {OrgRole.OWNER},
    "manage_settings":  {OrgRole.OWNER, OrgRole.ADMIN},
}


async def get_user_org_role(
    org_id,
    user: User,
    db: AsyncSession,
) -> OrgRole:
    """Fetch the role of a user within a specific organization."""
    result = await db.execute(
        select(OrganizationMember.role).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user.id,
        )
    )
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization",
        )
    return role


def require_permission(permission: str) -> Callable:
    """
    Dependency factory – returns a FastAPI dependency that asserts the
    current user has the given permission within the request's organization.

    Usage in a route:
        @router.post("/projects", dependencies=[Depends(require_permission("create_project"))])
    """
    allowed_roles = PERMISSION_MATRIX.get(permission, set())

    async def _checker(
        org_id,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        role = await get_user_org_role(org_id, current_user, db)
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: '{permission}' requires one of {[r.value for r in allowed_roles]}",
            )
        return role

    return _checker
