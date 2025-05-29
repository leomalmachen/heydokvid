"""
Heydok Video - Main FastAPI Application
HIPAA/GDPR compliant video conferencing system
"""

from contextlib import asynccontextmanager
import logging
from typing import Any, Dict

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import os

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.security import SecurityMiddleware, GDPRComplianceMiddleware


# Setup structured logging
setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle
    """
    # Startup
    logger.info("Starting Heydok Video Backend", version=settings.VERSION)
    
    # Initialize LiveKit client
    try:
        from app.core.livekit import livekit_client
        await livekit_client.initialize()
        logger.info("LiveKit client initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize LiveKit client", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("Shutting down Heydok Video Backend")


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

# Add security middleware
app.add_middleware(SecurityMiddleware)
app.add_middleware(GDPRComplianceMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


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
    Health check endpoint with system status
    """
    try:
        # Test LiveKit connection
        from app.core.livekit import livekit_client
        livekit_status = "healthy"
        try:
            await livekit_client.get_room_info("health-check-room")
        except Exception:
            livekit_status = "degraded"
        
        return {
            "status": "healthy",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "services": {
                "livekit": livekit_status,
                "api": "healthy"
            }
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "error": str(e)
        }


# Include API router
try:
    from app.api.v1.api import api_router
    app.include_router(api_router, prefix="/api/v1")
except Exception as e:
    logger.error("Failed to include API router", error=str(e))


# Frontend routing for meetings
@app.get("/meeting/{meeting_id}")
async def serve_meeting_page(meeting_id: str):
    """
    Serve meeting page for specific meeting ID
    """
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