"""
Health/readiness routes — used by Kubernetes liveness/readiness probes
and load balancers.
"""

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    """Liveness probe — just confirms the process is up."""
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


@router.get("/ready")
def readiness():
    """Readiness probe — confirms the DB connection is actually working."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:  # noqa: BLE001
        db_ok = False

    status_code = "ok" if db_ok else "degraded"
    return {"status": status_code, "database": "connected" if db_ok else "unreachable"}
