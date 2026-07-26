# ADR 0002 – Security Hardening, Rate Limiting, and Prometheus Observability

**Date:** 2026-07-25  
**Status:** Accepted  
**Deciders:** Sara (Tech Lead)

---

## Context

As CloudBoard approached production readiness, we needed to implement a security baseline, API abuse prevention, and infrastructure observability that scales beyond development mode.

## Decisions

### A. Security Headers Middleware (Module 16)

We implemented a custom `SecurityHeadersMiddleware` injecting the following headers on every HTTP response:

- `X-Content-Type-Options: nosniff` — Prevents MIME sniffing
- `X-Frame-Options: DENY` — Prevents clickjacking via iframes  
- `X-XSS-Protection: 1; mode=block` — Forces XSS filtering in legacy browsers
- `Content-Security-Policy: default-src 'self' ...` — Restricts resource loading origins
- `Referrer-Policy: strict-origin-when-cross-origin`

Additionally, all user-supplied string inputs are sanitized via `sanitize_input()` which HTML-encodes dangerous characters and strips `<script>` blocks.

### B. Sliding Window Token Bucket Rate Limiting (Module 13)

We chose an **in-process sliding window rate limiter** (`RateLimitMiddleware`) rather than a Redis-backed one for the MVP phase. It enforces 120 requests per minute per client IP:

- Zero external dependencies for local dev
- Exposes `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` headers
- Returns HTTP 429 with retry guidance when limit is exceeded

**Future Migration:** In production with multiple Uvicorn workers, this must be migrated to Redis using `redis.asyncio` sliding window counters.

### C. Prometheus Telemetry Exporter (Modules 11–12)

We exposed a plain-text Prometheus metrics endpoint at `/api/v1/system/metrics`. The metrics include:

- `cloudboard_uptime_seconds` (gauge)
- `cloudboard_requests_total` (counter)
- `cloudboard_request_errors_total` (counter)
- `cloudboard_websocket_connections` (gauge)

**Alternative considered:** `prometheus-client` library — rejected for MVP to avoid extra dependency. Will be adopted in v2 for full histogram/label support.

### D. Request Tracing Middleware

All HTTP responses receive:
- `X-Request-ID` (UUIDv4 per request)
- `X-Response-Time-MS` (elapsed processing time)

## Consequences

- All test clients must accept these headers; pytest TestClient does.
- Rate limiter state is **per-process** — load balanced deployments require Redis backend.
- CSP header currently set permissively (`unsafe-inline`) to support the Vite development server; should be tightened for production.
