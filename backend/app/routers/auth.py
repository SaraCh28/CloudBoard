"""
CloudBoard – Authentication Router (Module 16).

Endpoints: register, login, refresh, logout, change-password, me.
OAuth: Google skeleton (/auth/google, /auth/google/callback).

Security: All mutating endpoints write to the AuditLog table.
Password strength is validated via Pydantic field_validator.
"""

import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.auth.dependencies import get_current_user
from app.services.audit import audit

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
settings = get_settings()


# ── Schemas ──────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=64)
    display_name: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Enforce at least one uppercase, one digit, one special char."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", v):
            raise ValueError("Password must contain at least one special character.")
        return v

    @field_validator("username")
    @classmethod
    def username_alphanum(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username may only contain letters, digits, underscores, and hyphens.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def new_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", v):
            raise ValueError("Password must contain at least one special character.")
        return v


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    display_name: str
    avatar_url: str | None
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str


# ── Routes ───────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Create a new user account."""
    existing = await db.execute(
        select(User).where((User.email == body.email) | (User.username == body.username))
    )
    if existing.scalar_one_or_none():
        await audit.log(
            db, action="register", status="failure",
            detail=f"Email or username already in use: {body.email}", request=request,
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or username already in use")

    user = User(
        email=body.email,
        username=body.username,
        display_name=body.display_name,
        hashed_password=hash_password(body.password),
        is_verified=False,
    )
    db.add(user)
    await db.flush()

    await audit.log(
        db, action="register", status="success",
        user_id=str(user.id), username=user.username,
        resource_type="user", resource_id=str(user.id),
        detail=f"New account registered for {user.email}", request=request,
    )
    await db.commit()

    return _issue_tokens(user)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Authenticate with email + password."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        await audit.log(
            db, action="login", status="failure",
            detail=f"Invalid credentials for {body.email}", request=request,
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        await audit.log(
            db, action="login", status="failure",
            user_id=str(user.id), username=user.username,
            detail="Account deactivated", request=request,
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    user.last_login_at = datetime.now(timezone.utc)

    await audit.log(
        db, action="login", status="success",
        user_id=str(user.id), username=user.username,
        resource_type="user", resource_id=str(user.id),
        detail="Successful login", request=request,
    )
    await db.commit()

    return _issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for a new token pair."""
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = uuid.UUID(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return _issue_tokens(user)


@router.post("/logout", response_model=MessageResponse)
async def logout(request: Request, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Logout the current user.
    Token blacklisting via Redis is wired at the TODO below;
    for now the client discards tokens and we write an audit entry.
    """
    await audit.log(
        db, action="logout", status="success",
        user_id=str(current_user.id), username=current_user.username,
        resource_type="user", resource_id=str(current_user.id),
        detail="User logged out", request=request,
    )
    await db.commit()
    # TODO: Add token to Redis blacklist (Module 13)
    return {"message": f"User {current_user.username} logged out successfully"}


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    body: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change password for the authenticated user."""
    if not current_user.hashed_password or not verify_password(body.current_password, current_user.hashed_password):
        await audit.log(
            db, action="change_password", status="failure",
            user_id=str(current_user.id), username=current_user.username,
            detail="Incorrect current password supplied", request=request,
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    current_user.hashed_password = hash_password(body.new_password)
    await audit.log(
        db, action="change_password", status="success",
        user_id=str(current_user.id), username=current_user.username,
        detail="Password changed successfully", request=request,
    )
    await db.commit()
    return {"message": "Password changed successfully"}


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """Return the current authenticated user's profile."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
    )


# ── Google OAuth Skeleton ────────────────────────────────────────

@router.get("/google", tags=["OAuth"])
async def google_oauth_redirect():
    """
    Initiate Google OAuth2 authorization flow.

    In production: redirect to Google's authorization endpoint with
    client_id, redirect_uri, scope, state, and code_challenge (PKCE).
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )

    # Build the Google auth URL
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": "http://localhost:8005/api/v1/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    google_url = f"https://accounts.google.com/o/oauth2/v2/auth?{query}"

    return {"redirect_url": google_url}


@router.get("/google/callback", tags=["OAuth"])
async def google_oauth_callback(code: str, db: AsyncSession = Depends(get_db)):
    """
    Google OAuth2 callback handler.

    In production:
    1. Exchange `code` for access + id_token via Google Token endpoint.
    2. Verify id_token signature.
    3. Upsert user in `users` table (oauth_provider='google').
    4. Return CloudBoard JWT pair.

    Currently returns a stub response until GOOGLE_CLIENT_SECRET is set.
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth credentials not configured.",
        )

    # TODO: Exchange code → tokens → verify → upsert user → return JWT
    return {
        "message": "OAuth callback received.",
        "note": "Full token exchange not yet implemented – configure GOOGLE_CLIENT_ID/SECRET.",
        "code_received": bool(code),
    }


# ── Helpers ──────────────────────────────────────────────────────

def _issue_tokens(user: User) -> TokenResponse:
    data = {"sub": str(user.id)}
    return TokenResponse(
        access_token=create_access_token(data),
        refresh_token=create_refresh_token(data),
    )
