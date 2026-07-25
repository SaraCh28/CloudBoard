# CloudBoard

A full-stack engineering intelligence & project management platform built with **Vite + React** on the frontend and **FastAPI + SQLAlchemy** on the backend. Designed with a premium charcoal & gold UI, this platform features real-time collaboration, file attachments, GraphQL Gateway, AI assistance, full-text search, role-based access control (RBAC), and system observability with Prometheus metrics.

## Key Features & Modules

- **GraphQL Gateway (Module 7):** Single entry point query & mutation processing powered by **Strawberry GraphQL** with interactive GraphiQL IDE (`/graphql`).
- **Cache-Aside & Rate Limiting (Module 13):** In-memory/Redis cache-aside manager with TTL expiration alongside sliding window token bucket rate limiting (120 req/min per IP).
- **Security Hardening (Module 16):** Strict security response headers (`X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`) and input XSS sanitization.
- **WebSocket Real-time Collaboration (Module 8):** Live task updates, status sync, user presence indicators, and activity broadcasting across connected clients via WebSockets (`/ws/live`).
- **File Storage & Attachment Service (Module 9):** Task file attachment uploads, validation, download links, and static asset serving (`/api/v1/attachments`).
- **System Admin & Observability (Modules 10, 11 & 12):** Production-grade health checks (`/api/v1/system/health`), Prometheus telemetry exporter (`/api/v1/system/metrics`), and centralized audit log streaming.
- **Global Search Service (Module 6):** Full-text tsvector and semantic search across tasks, projects, organizations, and team members with instant navigation (`/api/v1/search`).
- **Full-Stack Kanban Board & Workflows:** Drag-and-drop task management, sprint tracking, and subtasks.
- **AI Co-Pilot (Gemini - Module 5):** Automated task estimation, duplicate task detection, subtask generation, and blocker predictions.
- **Role-Based Access Control (RBAC):** Granular user permissions (Owner, Admin, Manager, Developer, Viewer).
- **Analytics & Dashboards:** Workload distribution, burndown charts, velocity tracking, and health metrics powered by Recharts.

## Tech Stack

- **Frontend:** React, Vite, Tailwind/Vanilla CSS (Charcoal & Gold theme), Lucide Icons, Recharts, WebSocket client, GraphQL client.
- **Backend:** Python, FastAPI, Strawberry GraphQL, SQLAlchemy, Alembic Migrations, AsyncPG / SQLite, WebSockets, Passlib (Argon2), PyJWT, Prometheus Exporter.
- **DevOps & Infrastructure:** Docker, Docker Compose, GitHub Actions CI/CD pipeline, Nginx.

## Development Setup

### 1. Backend (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start the FastAPI server (runs on http://127.0.0.1:8005)
uvicorn app.main:app --reload --port 8005
```

### 2. Frontend (React/Vite)

```bash
# From the project root
npm install

# Start the Vite server (runs on http://127.0.0.1:5173)
npm run dev
```

### 3. API Documentation, Telemetry & GraphQL

- **Swagger API Docs:** `http://localhost:8005/docs`
- **GraphiQL IDE:** `http://localhost:8005/graphql`
- **Health Check:** `http://localhost:8005/api/v1/system/health`
- **Prometheus Metrics:** `http://localhost:8005/api/v1/system/metrics`
- **WebSocket Endpoint:** `ws://localhost:8005/ws/live`

## License

MIT © 2026 Sara
