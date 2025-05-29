"""
Meeting endpoints with LiveKit integration
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import secrets
import string
from typing import Dict, Any, Optional
from pydantic import BaseModel
import structlog

from app.core.livekit import get_livekit_client, LiveKitClient
from app.core.config import settings

logger = structlog.get_logger()
router = APIRouter()


class CreateMeetingResponse(BaseModel):
    meeting_id: str
    meeting_link: str
    created_at: str
    livekit_url: str


class JoinMeetingRequest(BaseModel):
    user_name: str


class JoinMeetingResponse(BaseModel):
    token: str
    meeting_id: str
    user_name: str
    livekit_url: str
    user_id: str


class MeetingInfoResponse(BaseModel):
    meeting_id: str
    exists: bool
    num_participants: int = 0
    created_at: Optional[str] = None
    max_participants: int = 50


@router.post("/create", response_model=CreateMeetingResponse)
async def create_meeting(
    livekit: LiveKitClient = Depends(get_livekit_client)
) -> CreateMeetingResponse:
    """
    Create a new meeting room
    
    This endpoint:
    1. Generates a unique meeting ID
    2. Creates a persistent room on the LiveKit server
    3. Returns a shareable meeting link
    """
    try:
        # Generate unique meeting ID
        meeting_id = livekit.generate_room_id()
        
        # Create room on LiveKit server
        room = await livekit.create_room(
            room_name=meeting_id,
            empty_timeout=3600,  # Room stays 1 hour after last participant
            max_participants=50,
            metadata={
                "created_at": datetime.utcnow().isoformat(),
                "created_by": "instant_meeting"
            }
        )
        
        # Generate meeting link
        # Use the frontend URL from settings
        meeting_link = f"{settings.FRONTEND_URL}/meeting/{meeting_id}"
        
        logger.info("Created meeting room",
                   meeting_id=meeting_id,
                   room_sid=room.get("sid"))
        
        return CreateMeetingResponse(
            meeting_id=meeting_id,
            meeting_link=meeting_link,
            created_at=datetime.utcnow().isoformat(),
            livekit_url=settings.LIVEKIT_URL
        )
        
    except Exception as e:
        logger.error("Failed to create meeting", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create meeting: {str(e)}"
        )


@router.post("/{meeting_id}/join", response_model=JoinMeetingResponse)
async def join_meeting(
    meeting_id: str,
    request: JoinMeetingRequest,
    livekit: LiveKitClient = Depends(get_livekit_client)
) -> JoinMeetingResponse:
    """
    Join an existing meeting
    
    This endpoint:
    1. Verifies the meeting exists
    2. Generates a unique user ID
    3. Creates an access token for the participant
    4. Returns the token and connection details
    """
    try:
        # Check if room exists on LiveKit server
        room = await livekit.get_room(meeting_id)
        if not room:
            logger.warning("Meeting not found", meeting_id=meeting_id)
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # Generate unique user ID
        user_id = f"{request.user_name.lower().replace(' ', '_')}_{secrets.token_hex(4)}"
        
        # Generate LiveKit access token
        token = livekit.generate_token(
            room_name=meeting_id,
            identity=user_id,
            name=request.user_name,
            metadata={"joined_at": datetime.utcnow().isoformat()},
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True
        )
        
        logger.info("User joined meeting",
                   meeting_id=meeting_id,
                   user_id=user_id,
                   user_name=request.user_name)
        
        return JoinMeetingResponse(
            token=token,
            meeting_id=meeting_id,
            user_name=request.user_name,
            livekit_url=settings.LIVEKIT_URL,
            user_id=user_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to join meeting", 
                    error=str(e),
                    meeting_id=meeting_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to join meeting: {str(e)}"
        )


@router.get("/{meeting_id}/info", response_model=MeetingInfoResponse)
async def get_meeting_info(
    meeting_id: str,
    livekit: LiveKitClient = Depends(get_livekit_client)
) -> MeetingInfoResponse:
    """
    Get information about a meeting
    
    This endpoint checks if a meeting exists and returns basic information
    """
    try:
        # Get room info from LiveKit
        room = await livekit.get_room(meeting_id)
        
        if room:
            return MeetingInfoResponse(
                meeting_id=meeting_id,
                exists=True,
                num_participants=room.get("num_participants", 0),
                created_at=room.get("creation_time"),
                max_participants=room.get("max_participants", 50)
            )
        else:
            return MeetingInfoResponse(
                meeting_id=meeting_id,
                exists=False
            )
            
    except Exception as e:
        logger.error("Failed to get meeting info",
                    error=str(e),
                    meeting_id=meeting_id)
        return MeetingInfoResponse(
            meeting_id=meeting_id,
            exists=False
        )


@router.get("/{meeting_id}/exists")
async def check_meeting_exists(
    meeting_id: str,
    livekit: LiveKitClient = Depends(get_livekit_client)
) -> Dict[str, Any]:
    """
    Quick check if a meeting exists
    """
    try:
        room = await livekit.get_room(meeting_id)
        return {
            "exists": room is not None,
            "meeting_id": meeting_id
        }
    except Exception as e:
        logger.error("Failed to check meeting",
                    error=str(e),
                    meeting_id=meeting_id)
        return {
            "exists": False,
            "meeting_id": meeting_id
        }


@router.delete("/{meeting_id}")
async def delete_meeting(
    meeting_id: str,
    livekit: LiveKitClient = Depends(get_livekit_client)
) -> Dict[str, Any]:
    """
    Delete a meeting room
    """
    try:
        # Check if room exists
        room = await livekit.get_room(meeting_id)
        if not room:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # Delete room
        success = await livekit.delete_room(meeting_id)
        
        if success:
            logger.info("Deleted meeting", meeting_id=meeting_id)
            return {
                "success": True,
                "message": "Meeting deleted successfully",
                "meeting_id": meeting_id
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete meeting"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete meeting",
                    error=str(e),
                    meeting_id=meeting_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete meeting: {str(e)}"
        )


@router.get("/{meeting_id}/participants")
async def list_participants(
    meeting_id: str,
    livekit: LiveKitClient = Depends(get_livekit_client)
) -> Dict[str, Any]:
    """
    List all participants in a meeting
    """
    try:
        # Check if room exists
        room = await livekit.get_room(meeting_id)
        if not room:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # Get participants
        participants = await livekit.list_participants(meeting_id)
        
        return {
            "meeting_id": meeting_id,
            "participants": participants,
            "count": len(participants)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list participants",
                    error=str(e),
                    meeting_id=meeting_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list participants: {str(e)}"
        ) 