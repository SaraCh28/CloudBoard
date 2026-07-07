# CloudBoard

A full-stack engineering management platform built with **Vite + React** on the frontend and **FastAPI + SQLite** on the backend. Designed with a premium charcoal & gold UI, this platform demonstrates how to build robust CRUD interfaces integrated with AI-driven workflows.

## Features

- **Full-Stack Kanban Board:** Drag-and-drop tasks across columns. State is persisted in a relational database (SQLite) via a FastAPI REST API.
- **Dashboard & Analytics:** Visualizes project health, developer workload, and sprint progress using Recharts.
- **AI Co-Pilot (Gemini):** Frontend-integrated AI heuristics for task estimation and duplicate detection. Gracefully degrades to local mock data if no API key is provided.
- **Role-Based Access Control (RBAC):** Simulated frontend settings panel for user roles (Owner, Manager, Developer).
- **Backend Architecture:** A FastAPI foundation built with SQLAlchemy ORM, Pydantic schemas, and JWT authentication scaffolds.

## Tech Stack

- **Frontend:** React, Vite, CSS (Charcoal & Gold theme), Lucide Icons, Recharts.
- **Backend:** Python, FastAPI, SQLAlchemy, SQLite (Development).

## Development Setup

To run this project locally, you will need to start both the frontend development server and the backend API server.

### 1. Backend (FastAPI)

Requires Python 3.10+.

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start the FastAPI server (runs on http://127.0.0.1:8000)
uvicorn app.main:app --reload
```
*Note: The SQLite database (`cloudboard.db`) and tables will be created automatically on the first run.*

### 2. Frontend (React/Vite)

Requires Node.js 18+.

```bash
# From the project root
npm install

# Start the Vite server (runs on http://127.0.0.1:5173)
npm run dev
```

### 3. Environment Variables (Optional)
To enable real AI integration on the frontend, create a `.env` file in the root directory (or expose it in your environment):
```
VITE_GEMINI_API_KEY=your_gemini_api_key_here
```

## Project Structure

- `/src`: React frontend application.
  - `/components`: Dashboard, KanbanBoard, Analytics, etc.
  - `/lib`: API client (`api.js`) and AI integration (`gemini.js`).
- `/backend`: FastAPI application.
  - `/app/models`: SQLAlchemy ORM models (Task, User, Organization).
  - `/app/routers`: REST endpoints.
- `docker-compose.yml` & `Dockerfile`: Infrastructure scaffolding for future production deployments.

## License
MIT © 2026 Sara
