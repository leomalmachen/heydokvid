"""
Main API router for v1 endpoints
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    rooms,
    users,
    webhooks,
    recordings,
    chat,
    meetings
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)

api_router.include_router(
    rooms.router,
    prefix="/rooms",
    tags=["rooms"]
)

api_router.include_router(
    meetings.router,
    prefix="/meetings",
    tags=["meetings"]
)

api_router.include_router(
    recordings.router,
    prefix="/recordings",
    tags=["recordings"]
)

api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["chat"]
)

api_router.include_router(
    webhooks.router,
    prefix="/webhooks",
    tags=["webhooks"]
) 