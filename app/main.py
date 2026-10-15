"""
Main FastAPI application entrypoint.
Wires together all routers, middleware, exception handlers, and startup hooks.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.auth_routes import router as auth_router
from app.api.chat_routes import router as chat_router
from app.api.health_routes import router as health_router
from app.api.kb_routes import router as kb_router
from app.api.ticket_routes import router as ticket_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.db.session import Base, engine

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "starting_application", env=settings.app_env, version=settings.app_version
    )
    # Create tables if they don't exist (use Alembic migrations in real production)
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("shutting_down_application")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Enterprise AI Customer Support Agent Platform — RAG + Agentic AI + MLOps",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics exposed at /metrics
Instrumentator().instrument(app).expose(app)

# Routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(ticket_router)
app.include_router(chat_router)
app.include_router(kb_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", path=str(request.url), error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred. Please try again later."},
    )


@app.get("/")
def root():
    return {
        "message": f"{settings.app_name} is running",
        "docs": "/docs",
        "health": "/health",
    }
