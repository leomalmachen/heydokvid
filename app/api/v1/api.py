"""
API v1 router with all endpoints
"""

from fastapi import APIRouter

from app.api.v1.endpoints import meetings, recordings

api_router = APIRouter()

# Include endpoints
api_router.include_router(meetings.router, prefix="/meetings", tags=["meetings"])
api_router.include_router(recordings.router, prefix="/recordings", tags=["recordings"]) 