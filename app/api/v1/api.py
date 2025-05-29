"""
API v1 router
"""

from fastapi import APIRouter

from app.api.v1.endpoints import meetings

api_router = APIRouter()

# Include endpoints
api_router.include_router(meetings.router, prefix="/meetings", tags=["meetings"]) 