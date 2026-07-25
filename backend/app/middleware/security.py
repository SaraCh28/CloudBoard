"""
CloudBoard – Security Hardening Middleware & Input Sanitizer (Module 16).
Injects security HTTP headers and provides HTML/Script input sanitization.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import re
import html


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to every outgoing HTTP response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: http: https: ws: wss:;"

        return response


def sanitize_input(text: str) -> str:
    """Sanitizes user input string against XSS injection attacks."""
    if not text:
        return ""
    # HTML entity encode dangerous characters
    clean = html.escape(text.strip())
    # Strip script tags if any slip through
    clean = re.sub(r'<script.*?>.*?</script>', '', clean, flags=re.DOTALL | re.IGNORECASE)
    return clean
