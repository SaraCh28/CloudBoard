"""
CloudBoard – Security Hardening Middleware & Input Sanitizer (Module 16).

Provides:
  • SecurityHeadersMiddleware  – injects security HTTP response headers
  • CSRFMiddleware             – double-submit cookie CSRF protection
  • sanitize_input()           – XSS/HTML sanitizer for user-supplied strings
  • validate_file_upload()     – MIME-type whitelist + size enforcement helper
"""

import re
import html
import secrets
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


# ── Security Headers ─────────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds hardened security headers to every outgoing HTTP response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        # Legacy XSS filter (still useful for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Strict referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # HSTS (enable in production behind TLS)
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        # Permissions policy – disable unneeded browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        # Content Security Policy – no unsafe-eval; allow WebSocket ws/wss
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data: blob: https:; "
            "connect-src 'self' ws: wss: https:; "
            "frame-ancestors 'none';"
        )

        return response


# ── CSRF Double-Submit Cookie ────────────────────────────────────

_CSRF_COOKIE_NAME = "cloudboard_csrf"
_CSRF_HEADER_NAME = "x-csrf-token"

# Endpoints that modify state and must be protected
_CSRF_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

# Paths that are explicitly exempt (public webhooks, OAuth callbacks)
_CSRF_EXEMPT_PREFIXES = (
    "/api/v1/auth",          # Auth endpoints use Bearer tokens, not cookies
    "/api/v1/auth/google",   # OAuth redirect – no cookie yet
    "/health",
    "/graphql",              # Protected by Bearer token; CSRF less relevant
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/tasks",         # Prototype: tasks are unauthenticated
    "/api/v1/system",        # Admin & observability endpoints
    "/api/v1/organizations", # Bearer-token protected; CSRF not applicable
    "/api/v1/search",        # Bearer-token protected; CSRF not applicable
    "/uploads",              # Static files
)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Double-submit cookie CSRF protection.

    On the first GET /  a random token is set in a non-HttpOnly cookie
    so the SPA JavaScript can read it and echo it back in the
    `X-CSRF-Token` header on every mutating request.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Safe methods don't need CSRF validation
        if request.method in _CSRF_SAFE_METHODS:
            response = await call_next(request)
            # Seed the cookie if not already present
            if _CSRF_COOKIE_NAME not in request.cookies:
                token = secrets.token_hex(32)
                response.set_cookie(
                    _CSRF_COOKIE_NAME,
                    token,
                    httponly=False,   # Must be readable by JS
                    samesite="strict",
                    secure=False,     # Set True behind HTTPS
                    max_age=3600 * 8,
                )
            return response

        # Exempt paths
        if any(request.url.path.startswith(p) for p in _CSRF_EXEMPT_PREFIXES):
            return await call_next(request)

        # Validate double-submit
        cookie_token = request.cookies.get(_CSRF_COOKIE_NAME)
        header_token = request.headers.get(_CSRF_HEADER_NAME)

        if not cookie_token or not header_token or not secrets.compare_digest(
            cookie_token, header_token
        ):
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing or invalid."},
            )

        return await call_next(request)


# ── XSS Input Sanitizer ──────────────────────────────────────────

def sanitize_input(text: str) -> str:
    """
    Sanitize a user-supplied string against XSS injection.

    Steps:
    1. Strip leading/trailing whitespace.
    2. HTML-entity encode dangerous characters (<, >, ", ', &).
    3. Remove any residual <script> blocks (defence-in-depth).
    4. Remove javascript: URI schemes.
    """
    if not text:
        return ""

    text = text.strip()
    # HTML entity encode
    clean = html.escape(text)
    # Strip any encoded/decoded script tags
    clean = re.sub(
        r"<\s*script.*?>.*?</\s*script\s*>", "", clean, flags=re.DOTALL | re.IGNORECASE
    )
    # Strip javascript: protocol references
    clean = re.sub(r"javascript\s*:", "", clean, flags=re.IGNORECASE)
    return clean


# ── File Upload Validator ────────────────────────────────────────

# Allowed MIME types → associated safe extensions
_ALLOWED_MIME_TYPES: dict[str, set[str]] = {
    "image/jpeg":       {".jpg", ".jpeg"},
    "image/png":        {".png"},
    "image/gif":        {".gif"},
    "image/svg+xml":    {".svg"},
    "image/webp":       {".webp"},
    "application/pdf":  {".pdf"},
    "text/plain":       {".txt", ".md"},
    "text/csv":         {".csv"},
    "application/json": {".json"},
    "application/zip":  {".zip"},
    "application/gzip": {".gz"},
}

_MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def validate_file_upload(
    *,
    filename: Optional[str],
    content_type: Optional[str],
    size_bytes: int,
    max_size_bytes: int = _MAX_FILE_SIZE_BYTES,
) -> tuple[bool, str]:
    """
    Validate a file upload against MIME whitelist and size limit.

    Returns
    -------
    (True, "")                       – file is acceptable
    (False, "human-readable reason") – file rejected
    """
    import os

    if not filename:
        return False, "Filename is required."

    ext = os.path.splitext(filename)[1].lower()
    mime = (content_type or "").lower().split(";")[0].strip()

    # Check MIME type is on the whitelist
    if mime not in _ALLOWED_MIME_TYPES:
        return False, f"Content-Type '{mime}' is not permitted."

    # Check extension matches the declared MIME type
    allowed_exts = _ALLOWED_MIME_TYPES[mime]
    if ext not in allowed_exts:
        return False, (
            f"File extension '{ext}' does not match declared type '{mime}'. "
            f"Expected one of: {', '.join(sorted(allowed_exts))}"
        )

    # Check size
    if size_bytes > max_size_bytes:
        limit_mb = max_size_bytes // (1024 * 1024)
        return False, f"File size {size_bytes // 1024} KB exceeds {limit_mb} MB limit."

    return True, ""
