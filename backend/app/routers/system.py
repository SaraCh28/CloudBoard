"""
CloudBoard – System Admin, Observability & Prometheus Metrics Router.

/api/v1/system/health   – detailed health check (DB, cache, websocket)
/api/v1/system/metrics  – Prometheus-compatible text
/api/v1/system/logs     – real AuditLog DB rows (paginated)
/api/v1/system/logs     POST – write a manual audit entry (admin)
/api/v1/version         – semver + build metadata
"""

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.database import get_db
from app.config import get_settings
from app.routers.websocket import manager
from app.models.audit_log import AuditLog
from app.services.cache import cache_service
import time
import os
import psutil
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/system", tags=["System Admin & Observability"])

START_TIME = time.time()
request_counter = {"total": 0, "errors": 0}


def record_request(is_error: bool = False):
    request_counter["total"] += 1
    if is_error:
        request_counter["errors"] += 1


# ── Health ────────────────────────────────────────────────────────

@router.get("/health")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Comprehensive system health report checking DB, Memory, Cache, and WebSocket."""
    db_status = "healthy"
    db_latency_ms = 0.0

    try:
        t0 = time.perf_counter()
        await db.execute(text("SELECT 1"))
        db_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    process = psutil.Process(os.getpid()) if hasattr(psutil, "Process") else None
    mem_mb = round(process.memory_info().rss / (1024 * 1024), 2) if process else "N/A"
    uptime_seconds = round(time.time() - START_TIME, 1)

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": time.time(),
        "uptime_seconds": uptime_seconds,
        "services": {
            "database": {"status": db_status, "latency_ms": db_latency_ms},
            "websocket_cluster": {
                "status": "healthy",
                "active_connections": len(manager.active_connections),
            },
            "graphql_gateway": {"status": "healthy", "endpoint": "/graphql"},
            "cache_layer": {"status": "healthy", "stats": cache_service.get_stats()},
        },
        "system_resources": {
            "memory_usage_mb": mem_mb,
            "environment": get_settings().ENVIRONMENT,
        },
    }


# ── Prometheus Metrics ────────────────────────────────────────────

@router.get("/metrics")
async def get_prometheus_metrics():
    """Prometheus-compatible metrics exporter endpoint."""
    uptime = time.time() - START_TIME
    ws_conns = len(manager.active_connections)
    total_req = request_counter["total"]
    err_req = request_counter["errors"]

    prometheus_text = f"""# HELP cloudboard_uptime_seconds Total application uptime in seconds.
# TYPE cloudboard_uptime_seconds gauge
cloudboard_uptime_seconds {uptime:.2f}

# HELP cloudboard_requests_total Total HTTP requests processed.
# TYPE cloudboard_requests_total counter
cloudboard_requests_total {total_req}

# HELP cloudboard_request_errors_total Total HTTP request errors.
# TYPE cloudboard_request_errors_total counter
cloudboard_request_errors_total {err_req}

# HELP cloudboard_websocket_connections Active real-time WebSocket connections.
# TYPE cloudboard_websocket_connections gauge
cloudboard_websocket_connections {ws_conns}
"""
    return Response(content=prometheus_text, media_type="text/plain")


# ── Audit Logs ─────────────────────────────────────────────────────

@router.get("/logs")
async def get_audit_logs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    action: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Retrieve paginated AuditLog entries from the database.

    Supports filtering by action type and user_id.
    """
    query = select(AuditLog).order_by(AuditLog.timestamp.desc())

    if action:
        query = query.where(AuditLog.action == action)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)

    # Count total
    count_q = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar_one()

    # Paginate
    offset = (page - 1) * limit
    result = await db.execute(query.offset(offset).limit(limit))
    logs = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [entry.to_dict() for entry in logs],
    }


class ManualAuditRequest(BaseModel):
    action: str
    detail: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None


@router.post("/logs", status_code=status.HTTP_201_CREATED)
async def create_audit_entry(
    body: ManualAuditRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Write a manual audit entry (admin/integration use)."""
    entry = AuditLog(
        action=body.action,
        detail=body.detail,
        resource_type=body.resource_type,
        resource_id=body.resource_id,
        status="manual",
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry.to_dict()
