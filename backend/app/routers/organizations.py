"""
CloudBoard – Organizations Router.

Endpoints: create, list, get, update, invite, accept-invite, remove-member,
           transfer-ownership, delete.
"""

import re
import uuid
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.organization import Organization, OrganizationMember, Invitation, OrgRole, InvitationStatus
from app.auth.dependencies import get_current_user
from app.auth.rbac import get_user_org_role, PERMISSION_MATRIX

router = APIRouter(prefix="/api/v1/organizations", tags=["Organizations"])


# ── Schemas ──────────────────────────────────────────────────────
class CreateOrgRequest(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    description: str | None = None


class UpdateOrgRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=128)
    description: str | None = None


class OrgResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None
    is_active: bool
    created_at: datetime
    member_count: int = 0

    model_config = {"from_attributes": True}


class MemberResponse(BaseModel):
    id: str
    user_id: str
    username: str
    display_name: str
    email: str
    role: str
    joined_at: datetime


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = "developer"


class InviteResponse(BaseModel):
    id: str
    email: str
    role: str
    token: str
    status: str
    expires_at: datetime


class AcceptInviteRequest(BaseModel):
    token: str


class TransferRequest(BaseModel):
    new_owner_id: str


class MessageResponse(BaseModel):
    message: str


# ── Helpers ──────────────────────────────────────────────────────
def _slugify(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name.lower().strip())
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug[:64] + "-" + secrets.token_hex(3)


async def _assert_role(db, org_id, user, allowed_roles):
    role = await get_user_org_role(org_id, user, db)
    if role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return role


# ── Routes ───────────────────────────────────────────────────────
@router.post("/", response_model=OrgResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    body: CreateOrgRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new organization. The creator becomes the Owner."""
    org = Organization(
        name=body.name,
        slug=_slugify(body.name),
        description=body.description,
    )
    db.add(org)
    await db.flush()

    # Add creator as Owner
    membership = OrganizationMember(
        organization_id=org.id,
        user_id=current_user.id,
        role=OrgRole.OWNER,
    )
    db.add(membership)
    await db.flush()

    return OrgResponse(
        id=str(org.id), name=org.name, slug=org.slug,
        description=org.description, is_active=org.is_active,
        created_at=org.created_at, member_count=1,
    )


@router.get("/", response_model=list[OrgResponse])
async def list_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all organizations the current user is a member of."""
    result = await db.execute(
        select(Organization, func.count(OrganizationMember.id).label("member_count"))
        .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
        .where(OrganizationMember.user_id == current_user.id)
        .group_by(Organization.id)
    )
    rows = result.all()
    return [
        OrgResponse(
            id=str(org.id), name=org.name, slug=org.slug,
            description=org.description, is_active=org.is_active,
            created_at=org.created_at, member_count=count,
        )
        for org, count in rows
    ]


@router.get("/{org_id}", response_model=OrgResponse)
async def get_organization(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get organization details (must be a member)."""
    await get_user_org_role(org_id, current_user, db)

    result = await db.execute(
        select(Organization, func.count(OrganizationMember.id))
        .outerjoin(OrganizationMember)
        .where(Organization.id == org_id)
        .group_by(Organization.id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Organization not found")

    org, count = row
    return OrgResponse(
        id=str(org.id), name=org.name, slug=org.slug,
        description=org.description, is_active=org.is_active,
        created_at=org.created_at, member_count=count,
    )


@router.patch("/{org_id}", response_model=OrgResponse)
async def update_organization(
    org_id: uuid.UUID,
    body: UpdateOrgRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update organization settings (admin+ only)."""
    await _assert_role(db, org_id, current_user, {OrgRole.OWNER, OrgRole.ADMIN})

    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if body.name is not None:
        org.name = body.name
    if body.description is not None:
        org.description = body.description

    count_result = await db.execute(
        select(func.count(OrganizationMember.id)).where(OrganizationMember.organization_id == org_id)
    )
    count = count_result.scalar()

    return OrgResponse(
        id=str(org.id), name=org.name, slug=org.slug,
        description=org.description, is_active=org.is_active,
        created_at=org.created_at, member_count=count,
    )


@router.get("/{org_id}/members", response_model=list[MemberResponse])
async def list_members(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all members of an organization."""
    await get_user_org_role(org_id, current_user, db)

    result = await db.execute(
        select(OrganizationMember, User)
        .join(User, OrganizationMember.user_id == User.id)
        .where(OrganizationMember.organization_id == org_id)
    )
    rows = result.all()
    return [
        MemberResponse(
            id=str(m.id), user_id=str(m.user_id),
            username=u.username, display_name=u.display_name,
            email=u.email, role=m.role.value, joined_at=m.joined_at,
        )
        for m, u in rows
    ]


@router.post("/{org_id}/invite", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    org_id: uuid.UUID,
    body: InviteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Invite a user by email to join the organization."""
    await _assert_role(db, org_id, current_user, {OrgRole.OWNER, OrgRole.ADMIN, OrgRole.MANAGER})

    try:
        role = OrgRole(body.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {body.role}")

    token = secrets.token_urlsafe(48)
    invitation = Invitation(
        organization_id=org_id,
        email=body.email,
        role=role,
        invited_by=current_user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(invitation)
    await db.flush()

    # TODO: Send invitation email (Module 3 – Notification Service)

    return InviteResponse(
        id=str(invitation.id), email=invitation.email,
        role=invitation.role.value, token=token,
        status=invitation.status.value, expires_at=invitation.expires_at,
    )


@router.post("/accept-invite", response_model=MessageResponse)
async def accept_invitation(
    body: AcceptInviteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Accept a pending invitation using its token."""
    result = await db.execute(
        select(Invitation).where(
            Invitation.token == body.token,
            Invitation.status == InvitationStatus.PENDING,
        )
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found or already used")

    if invitation.expires_at < datetime.now(timezone.utc):
        invitation.status = InvitationStatus.EXPIRED
        raise HTTPException(status_code=410, detail="Invitation has expired")

    if invitation.email != current_user.email:
        raise HTTPException(status_code=403, detail="This invitation was sent to a different email address")

    # Check if already a member
    existing = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == invitation.organization_id,
            OrganizationMember.user_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        invitation.status = InvitationStatus.ACCEPTED
        return {"message": "You are already a member of this organization"}

    membership = OrganizationMember(
        organization_id=invitation.organization_id,
        user_id=current_user.id,
        role=invitation.role,
    )
    db.add(membership)
    invitation.status = InvitationStatus.ACCEPTED

    return {"message": "Successfully joined the organization"}


@router.delete("/{org_id}/members/{user_id}", response_model=MessageResponse)
async def remove_member(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a member from the organization (admin+ only). Cannot remove the owner."""
    await _assert_role(db, org_id, current_user, {OrgRole.OWNER, OrgRole.ADMIN})

    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if member.role == OrgRole.OWNER:
        raise HTTPException(status_code=400, detail="Cannot remove the organization owner. Transfer ownership first.")

    await db.delete(member)
    return {"message": "Member removed successfully"}


@router.post("/{org_id}/transfer-ownership", response_model=MessageResponse)
async def transfer_ownership(
    org_id: uuid.UUID,
    body: TransferRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Transfer organization ownership to another member (owner only)."""
    await _assert_role(db, org_id, current_user, {OrgRole.OWNER})

    new_owner_id = uuid.UUID(body.new_owner_id)

    # Get new owner membership
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == new_owner_id,
        )
    )
    new_owner_member = result.scalar_one_or_none()
    if not new_owner_member:
        raise HTTPException(status_code=404, detail="Target user is not a member of this organization")

    # Demote current owner to admin
    current_result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == current_user.id,
        )
    )
    current_member = current_result.scalar_one()
    current_member.role = OrgRole.ADMIN

    # Promote new owner
    new_owner_member.role = OrgRole.OWNER

    return {"message": "Ownership transferred successfully"}


@router.delete("/{org_id}", response_model=MessageResponse)
async def delete_organization(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an organization (owner only). This cascades to all projects."""
    await _assert_role(db, org_id, current_user, {OrgRole.OWNER})

    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    await db.delete(org)
    return {"message": f"Organization '{org.name}' deleted permanently"}
