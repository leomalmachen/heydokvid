"""
Simple meetings API endpoints - Google Meet style
"""

from typing import Optional
from datetime import datetime, timedelta
import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.livekit import get_livekit_client, LiveKitClient
from app.core.config import settings
from app.core.logging import get_logger
from app.models.room import Room, RoomStatus
from app.schemas.meeting import (
    SimpleMeetingCreate,
    SimpleMeetingResponse,
    SimpleMeetingJoin,
    SimpleMeetingTokenResponse
)

router = APIRouter()
logger = get_logger(__name__)


def generate_meeting_id() -> str:
    """Generate a Google Meet style meeting ID (xxx-xxxx-xxx)"""
    chars = string.ascii_lowercase + string.digits
    parts = [
        ''.join(secrets.choice(chars) for _ in range(3)),
        ''.join(secrets.choice(chars) for _ in range(4)),
        ''.join(secrets.choice(chars) for _ in range(3))
    ]
    return '-'.join(parts)


@router.post("/create", response_model=SimpleMeetingResponse)
async def create_instant_meeting(
    meeting_data: Optional[SimpleMeetingCreate] = None,
    db: AsyncSession = Depends(get_db),
    livekit: LiveKitClient = Depends(get_livekit_client)
) -> SimpleMeetingResponse:
    """
    Create an instant meeting - no authentication required
    """
    # Generate unique meeting ID
    meeting_id = generate_meeting_id()
    
    # Ensure meeting ID is unique in database
    while await db.scalar(select(Room).where(Room.room_id == meeting_id)):
        meeting_id = generate_meeting_id()
    
    logger.info("Creating new meeting", meeting_id=meeting_id)
    
    # Create room in LiveKit first
    try:
        livekit_room = await livekit.create_room(
            name=meeting_id,
            empty_timeout=300,  # 5 minutes
            max_participants=100,
            metadata='{"type": "instant_meeting", "created_at": "' + datetime.utcnow().isoformat() + '"}'
        )
        logger.info("LiveKit room created successfully", 
                   meeting_id=meeting_id, room_sid=livekit_room.sid)
    except Exception as e:
        logger.error("Failed to create LiveKit room", meeting_id=meeting_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create meeting room: {str(e)}"
        )
    
    # Create room in database
    room = Room(
        room_id=meeting_id,
        name=meeting_data.name if meeting_data and meeting_data.name else f"Meeting {meeting_id}",
        status=RoomStatus.ACTIVE,
        max_participants=100,
        enable_recording=False,
        enable_chat=True,
        enable_screen_share=True,
        waiting_room_enabled=False,
        metadata={"type": "instant_meeting", "livekit_sid": livekit_room.sid}
    )
    
    try:
        db.add(room)
        await db.commit()
        await db.refresh(room)
        logger.info("Database room created successfully", meeting_id=meeting_id, db_id=room.id)
    except Exception as e:
        logger.error("Failed to create database room", meeting_id=meeting_id, error=str(e))
        # Try to clean up LiveKit room
        try:
            await livekit.delete_room(meeting_id)
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save meeting to database"
        )
    
    # Generate meeting URL
    meeting_url = f"{settings.FRONTEND_URL}/meeting/{meeting_id}"
    
    logger.info("Meeting created successfully", 
               meeting_id=meeting_id, meeting_url=meeting_url)
    
    return SimpleMeetingResponse(
        meeting_id=meeting_id,
        meeting_url=meeting_url,
        created_at=room.created_at,
        expires_at=room.created_at + timedelta(hours=24)
    )


@router.post("/{meeting_id}/join", response_model=SimpleMeetingTokenResponse)
async def join_meeting(
    meeting_id: str,
    join_data: SimpleMeetingJoin,
    db: AsyncSession = Depends(get_db),
    livekit: LiveKitClient = Depends(get_livekit_client)
) -> SimpleMeetingTokenResponse:
    """
    Join a meeting - no authentication required
    """
    logger.info("Attempting to join meeting", 
               meeting_id=meeting_id, display_name=join_data.display_name)
    
    # Get room from database
    room = await db.scalar(
        select(Room).where(Room.room_id == meeting_id)
    )
    
    if not room:
        logger.warning("Meeting not found in database", meeting_id=meeting_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Check if room is active
    if room.status != RoomStatus.ACTIVE:
        logger.warning("Meeting not active", meeting_id=meeting_id, status=room.status)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting has ended or is not active"
        )
    
    # Verify LiveKit room exists
    try:
        livekit_room = await livekit.get_room(meeting_id)
        if not livekit_room:
            logger.warning("LiveKit room not found", meeting_id=meeting_id)
            # Try to recreate the room
            await livekit.create_room(
                name=meeting_id,
                empty_timeout=300,
                max_participants=room.max_participants,
                metadata='{"type": "instant_meeting", "recreated": true}'
            )
            logger.info("LiveKit room recreated", meeting_id=meeting_id)
    except Exception as e:
        logger.error("Failed to verify/create LiveKit room", 
                    meeting_id=meeting_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Meeting room is not available"
        )
    
    # Generate participant ID
    participant_id = f"guest-{secrets.token_hex(8)}"
    
    # Generate LiveKit token
    try:
        token = livekit.create_participant_token(
            room_name=meeting_id,
            user_id=participant_id,
            user_name=join_data.display_name,
            role="participant",
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True
        )
        logger.info("Token generated successfully", 
                   meeting_id=meeting_id, participant_id=participant_id)
    except Exception as e:
        logger.error("Failed to generate token", 
                    meeting_id=meeting_id, participant_id=participant_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate access token"
        )
    
    return SimpleMeetingTokenResponse(
        token=token,
        meeting_id=meeting_id,
        livekit_url=settings.LIVEKIT_URL,
        participant_id=participant_id
    )


@router.get("/{meeting_id}/info", response_model=SimpleMeetingResponse)
async def get_meeting_info(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
    livekit: LiveKitClient = Depends(get_livekit_client)
) -> SimpleMeetingResponse:
    """
    Get meeting information - no authentication required
    """
    logger.info("Getting meeting info", meeting_id=meeting_id)
    
    # Get room from database
    room = await db.scalar(
        select(Room).where(Room.room_id == meeting_id)
    )
    
    if not room:
        logger.warning("Meeting not found", meeting_id=meeting_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Check LiveKit room status
    try:
        livekit_room = await livekit.get_room(meeting_id)
        if not livekit_room and room.status == RoomStatus.ACTIVE:
            # Room exists in DB but not in LiveKit - mark as ended
            room.status = RoomStatus.ENDED
            await db.commit()
            logger.info("Meeting marked as ended (LiveKit room not found)", meeting_id=meeting_id)
    except Exception as e:
        logger.error("Failed to check LiveKit room status", 
                    meeting_id=meeting_id, error=str(e))
    
    meeting_url = f"{settings.FRONTEND_URL}/meeting/{meeting_id}"
    
    return SimpleMeetingResponse(
        meeting_id=meeting_id,
        meeting_url=meeting_url,
        created_at=room.created_at,
        expires_at=room.created_at + timedelta(hours=24),
        status=room.status
    )


@router.get("/{meeting_id}/exists")
async def check_meeting_exists(
    meeting_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Check if a meeting exists and is active
    """
    room = await db.scalar(
        select(Room).where(Room.room_id == meeting_id)
    )
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    if room.status != RoomStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Meeting has ended"
        )
    
    return {"exists": True, "status": room.status}


@router.delete("/{meeting_id}")
async def end_meeting(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
    livekit: LiveKitClient = Depends(get_livekit_client)
):
    """
    End a meeting
    """
    logger.info("Ending meeting", meeting_id=meeting_id)
    
    # Get room from database
    room = await db.scalar(
        select(Room).where(Room.room_id == meeting_id)
    )
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # End room in database
    room.status = RoomStatus.ENDED
    room.actual_end = datetime.utcnow()
    
    # Try to delete LiveKit room
    try:
        await livekit.delete_room(meeting_id)
        logger.info("LiveKit room deleted", meeting_id=meeting_id)
    except Exception as e:
        logger.warning("Failed to delete LiveKit room", 
                      meeting_id=meeting_id, error=str(e))
    
    await db.commit()
    logger.info("Meeting ended successfully", meeting_id=meeting_id)
    
    return {"message": "Meeting ended successfully"} 