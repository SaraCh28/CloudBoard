# ADR 0001 – FastAPI + React + SQLAlchemy Architecture Selection

**Date:** 2026-07-25  
**Status:** Accepted  
**Deciders:** Sara (Tech Lead)

---

## Context

CloudBoard is an engineering intelligence and project management platform requiring a high-performance, real-time capable backend paired with a responsive single-page frontend. We needed to select a backend framework, database ORM, and frontend library that could support WebSockets, async I/O, and complex relational data models.

## Decision

We selected the following core stack:

| Layer | Technology | Rationale |
|---|---|---|
| Backend Framework | **FastAPI (Python 3.12)** | Native async, built-in OpenAPI docs, Pydantic validation, WebSocket support |
| ORM | **SQLAlchemy 2.0 (Async)** | Production-grade, type-safe async sessions, supports PostgreSQL and SQLite |
| Database | **PostgreSQL (prod) / SQLite (dev/test)** | ACID-compliant relational DB; SQLite for zero-config local testing |
| Frontend | **React 18 + Vite** | Fast HMR, modern JSX, component model fits Kanban-style UI |
| Styling | **Vanilla CSS** | Full control, no build-time dependency, consistent design tokens |
| Realtime | **FastAPI WebSockets** | Native support, integrates with ASGI lifecycle |

## Alternatives Considered

- **Django**: Mature but synchronous by default; WebSocket support requires channels addon.
- **Node.js / Express**: Good for WS but Python ecosystem better for AI/ML integration (Gemini).
- **Next.js (Full-Stack)**: Considered but overkill for a monorepo split architecture.

## Consequences

- All database sessions must use `async with` patterns.
- SQLite used for unit/integration tests via `aiosqlite` driver (no PostgreSQL needed locally).
- A Vite dev proxy is recommended in production to avoid CORS issues.
