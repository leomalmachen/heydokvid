"""
Heydok Video - Main FastAPI Application
HIPAA/GDPR compliant video conferencing system
"""

from contextlib import asynccontextmanager
import logging
from typing import Any, Dict

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import structlog
import os

from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging import setup_logging
from app.api.v1.api import api_router
from app.core.security import SecurityMiddleware
from app.core.audit import AuditMiddleware


# Setup structured logging
setup_logging()
logger = structlog.get_logger()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle
    """
    # Startup
    logger.info("Starting Heydok Video Backend", version=settings.VERSION)
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize LiveKit client
    from app.core.livekit import livekit_client
    await livekit_client.initialize()
    
    # Initialize Redis
    from app.core.redis import redis_client
    await redis_client.initialize()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Heydok Video Backend")
    
    # Close connections
    await redis_client.close()
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title="Heydok Video API",
    description="HIPAA/GDPR compliant video conferencing API",
    version=settings.VERSION,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add rate limit exceeded handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security Middleware
app.add_middleware(SecurityMiddleware)

# Audit Middleware
app.add_middleware(AuditMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Trusted Host Middleware
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Prometheus metrics
if settings.PROMETHEUS_ENABLED:
    instrumentator = Instrumentator()
    instrumentator.instrument(app).expose(app, endpoint="/metrics")


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.error("Value error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


# Include API router
app.include_router(api_router, prefix="/api/v1")

# Frontend routing for meetings
@app.get("/meeting/{meeting_id}")
async def serve_meeting_page(meeting_id: str):
    """
    Serve meeting page for specific meeting ID
    """
    # In production, this would serve the React app
    # For now, return a simple response that can be used for testing
    return {
        "meeting_id": meeting_id,
        "message": f"Meeting page for {meeting_id}",
        "frontend_url": f"{settings.FRONTEND_URL}/meeting/{meeting_id}",
        "api_endpoints": {
            "join": f"/api/v1/meetings/{meeting_id}/join",
            "info": f"/api/v1/meetings/{meeting_id}/info",
            "exists": f"/api/v1/meetings/{meeting_id}/exists"
        }
    }

# Mount frontend build directory - DISABLED FOR NOW
# frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "build")
# app.mount("/static", StaticFiles(directory=os.path.join(frontend_path, "static")), name="static")

# Serve frontend - DISABLED FOR NOW
# @app.get("/{full_path:path}")
# async def serve_frontend(full_path: str):
#     file_path = os.path.join(frontend_path, "index.html")
#     if os.path.exists(file_path):
#         return FileResponse(file_path)
#     raise HTTPException(status_code=404, detail="Not found")


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "message": "Heydok Video API",
        "version": settings.VERSION,
        "docs": "/api/docs" if settings.DEBUG else None,
        "endpoints": {
            "create_meeting": "/api/v1/meetings/create",
            "health": "/health"
        }
    } 