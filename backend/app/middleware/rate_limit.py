"""
CloudBoard – Sliding Window Rate Limiting Middleware (Module 13 & 16).
Enforces API rate limits per client IP address using sliding window token buckets.
"""

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
from typing import Dict, List, Tuple


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding Window Rate Limiter for FastAPI."""

    def __init__(self, app, max_requests: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Stores IP address -> list of request timestamps [(timestamp)]
        self.client_requests: Dict[str, List[float]] = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        # Exclude static files and health check from strict rate limits
        if request.url.path.startswith("/uploads") or request.url.path == "/health":
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()

        if client_ip not in self.client_requests:
            self.client_requests[client_ip] = []

        # Remove requests older than the sliding window
        window_start = now - self.window_seconds
        timestamps = [ts for ts in self.client_requests[client_ip] if ts > window_start]
        self.client_requests[client_ip] = timestamps

        if len(timestamps) >= self.max_requests:
            reset_time = int(self.window_seconds - (now - timestamps[0]))
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Please wait before retrying.", "reset_in_seconds": reset_time},
                headers={
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time)
                }
            )

        # Record current request timestamp
        self.client_requests[client_ip].append(now)
        remaining = self.max_requests - len(self.client_requests[client_ip])

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(self.window_seconds)

        return response
