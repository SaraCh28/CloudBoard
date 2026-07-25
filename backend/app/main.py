import time
import uuid
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import engine, Base
from app.routers.auth import router as auth_router
from app.routers.organizations import router as org_router
from app.routers.tasks import router as tasks_router
from app.routers.search import router as search_router
from app.routers.websocket import router as websocket_router
from app.routers.attachments import router as attachments_router
from app.routers.system import router as system_router, record_request

# Import all models so SQLAlchemy registers them
from app.models import User, Organization, OrganizationMember, Invitation, Project, Task  # noqa: F401

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    # Create uploads directory if missing
    uploads_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    os.makedirs(uploads_path, exist_ok=True)

    if settings.ENVIRONMENT == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Engineering Intelligence Platform – Full Stack MVP (Auth, Projects, Real-time Collab, Attachments, Search & System Observability)",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware: Request Tracing & Timing ─────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()
    try:
        response = await call_next(request)
        record_request(is_error=response.status_code >= 400)
    except Exception as exc:
        record_request(is_error=True)
        raise exc from None

    process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-MS"] = str(process_time_ms)
    return response


# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static Uploads ────────────────────────────────────────────────
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

from app.routers.graphql import graphql_app
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security import SecurityHeadersMiddleware

# ── Middleware: Security & Rate Limiting ─────────────────────────
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=120, window_seconds=60)

# ── Routers ──────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(org_router)
app.include_router(tasks_router)
app.include_router(search_router)
app.include_router(websocket_router)
app.include_router(attachments_router)
app.include_router(system_router)
app.include_router(graphql_app, prefix="/graphql")


# ── Health check ─────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


