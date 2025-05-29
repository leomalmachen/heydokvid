"""
Meeting endpoints with enhanced LiveKit integration and security
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timedelta
import secrets
import string
from typing import Dict, Any, Optional
import structlog
from pydantic import BaseModel, Field

from app.core.livekit import livekit_client
from app.core.config import settings
from app.core.security import get_current_user_optional, rate_limit
from app.models.user import User, UserRole

logger = structlog.get_logger()
router = APIRouter()


class CreateMeetingRequest(BaseModel):
    """Request schema for creating a meeting"""
    name: Optional[str] = Field(None, description="Optional meeting name")
    max_participants: int = Field(10, ge=2, le=50, description="Maximum participants (2-50)")
    enable_recording: bool = Field(False, description="Enable recording capability")
    enable_chat: bool = Field(True, description="Enable chat functionality")
    enable_screen_share: bool = Field(True, description="Enable screen sharing")
    scheduled_start: Optional[datetime] = Field(None, description="Scheduled start time")
    scheduled_end: Optional[datetime] = Field(None, description="Scheduled end time")


class JoinMeetingRequest(BaseModel):
    """Request schema for joining a meeting"""
    user_name: str = Field(..., min_length=1, max_length=100, description="Display name")
    user_role: Optional[str] = Field("patient", description="User role (patient/physician)")
    enable_video: bool = Field(True, description="Join with video enabled")
    enable_audio: bool = Field(True, description="Join with audio enabled")


class MeetingResponse(BaseModel):
    """Response schema for meeting operations"""
    meeting_id: str
    meeting_link: str
    created_at: str
    livekit_url: str
    success: bool
    expires_at: Optional[str] = None


class JoinMeetingResponse(BaseModel):
    """Response schema for joining a meeting"""
    token: str
    meeting_id: str
    user_name: str
    livekit_url: str
    user_id: str
    success: bool
    expires_at: str
    permissions: Dict[str, bool]


def generate_room_id() -> str:
    """Generate a secure, unique room ID"""
    # Use cryptographically secure random generation
    parts = []
    for length in [3, 4, 3]:
        part = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(length))
        parts.append(part)
    return '-'.join(parts)


def validate_meeting_name(name: str) -> str:
    """Validate and sanitize meeting name"""
    if not name:
        return f"Meeting-{datetime.utcnow().strftime('%Y%m%d-%H%M')}"
    
    # Remove potentially harmful characters
    sanitized = ''.join(c for c in name if c.isalnum() or c in ' -_()[]')
    return sanitized[:100]  # Limit length


@router.post("/create", response_model=MeetingResponse)
@rate_limit(calls=10, period=60)  # 10 calls per minute
async def create_meeting(
    request: CreateMeetingRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    http_request: Request = None
) -> MeetingResponse:
    """
    Create a new meeting room with enhanced security
    
    This endpoint:
    1. Validates user permissions (if authenticated)
    2. Generates a unique, secure meeting ID
    3. Creates a persistent room on the LiveKit server
    4. Returns a shareable meeting link with expiration
    5. Logs the action for audit trail
    """
    try:
        # Validate permissions for recording
        if request.enable_recording and current_user:
            if not current_user.can_record:
                raise HTTPException(
                    status_code=403,
                    detail="Recording permission required"
                )
        
        # Validate scheduled times
        if request.scheduled_start and request.scheduled_end:
            if request.scheduled_end <= request.scheduled_start:
                raise HTTPException(
                    status_code=400,
                    detail="End time must be after start time"
                )
        
        # Generate unique meeting ID
        meeting_id = generate_room_id()
        
        # Validate and sanitize meeting name
        meeting_name = validate_meeting_name(request.name)
        
        # Create room on LiveKit server with enhanced configuration
        room = await livekit_client.create_room(
            room_name=meeting_id,
            max_participants=request.max_participants,
            enable_recording=request.enable_recording
        )
        
        # Generate meeting link
        meeting_link = f"{settings.FRONTEND_URL}/meeting/{meeting_id}"
        
        # Calculate expiration (24 hours from now)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Log the action
        logger.info("Meeting created",
                   meeting_id=meeting_id,
                   room_sid=room.get("sid"),
                   created_by=current_user.id if current_user else "anonymous",
                   max_participants=request.max_participants,
                   enable_recording=request.enable_recording,
                   client_ip=http_request.client.host if http_request else None)
        
        return MeetingResponse(
            meeting_id=meeting_id,
            meeting_link=meeting_link,
            created_at=datetime.utcnow().isoformat(),
            livekit_url=settings.LIVEKIT_URL,
            success=True,
            expires_at=expires_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create meeting", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create meeting: {str(e)}"
        )


@router.post("/{meeting_id}/join", response_model=JoinMeetingResponse)
@rate_limit(calls=20, period=60)  # 20 calls per minute
async def join_meeting(
    meeting_id: str, 
    request: JoinMeetingRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    http_request: Request = None
) -> JoinMeetingResponse:
    """
    Join an existing meeting with enhanced security
    
    This endpoint:
    1. Validates the meeting exists and is accessible
    2. Generates a unique user ID with role-based permissions
    3. Creates a secure, time-limited access token
    4. Returns connection details and user permissions
    5. Logs the join action for audit trail
    """
    try:
        # Validate meeting ID format
        if not meeting_id or len(meeting_id) < 5:
            raise HTTPException(status_code=400, detail="Invalid meeting ID format")
        
        # Check if room exists
        room_info = await livekit_client.get_room_info(meeting_id)
        if not room_info:
            logger.warning("Meeting not found", meeting_id=meeting_id)
            raise HTTPException(status_code=404, detail="Meeting not found or expired")
        
        # Check room capacity
        current_participants = room_info.get("num_participants", 0)
        max_participants = room_info.get("max_participants", 10)
        
        if current_participants >= max_participants:
            raise HTTPException(
                status_code=409, 
                detail="Meeting is full"
            )
        
        # Validate and sanitize user name
        user_name = request.user_name.strip()
        if len(user_name) < 1:
            raise HTTPException(status_code=400, detail="User name is required")
        
        # Generate unique user ID
        user_id = f"{user_name.lower().replace(' ', '_')}_{secrets.token_hex(4)}"
        
        # Determine user role and permissions
        user_role = request.user_role
        if current_user:
            user_role = current_user.role.value
        
        # Set permissions based on role
        can_publish = True
        can_subscribe = True
        can_publish_data = True
        
        # Physicians get additional permissions
        if user_role == "physician":
            can_publish = True
            can_subscribe = True
            can_publish_data = True
        elif user_role == "patient":
            can_publish = True
            can_subscribe = True
            can_publish_data = False  # Patients can't send data messages by default
        
        # Generate LiveKit access token with role-based permissions
        token = await livekit_client.generate_token(
            room_name=meeting_id,
            participant_name=user_name,
            user_role=user_role,
            can_publish=can_publish,
            can_subscribe=can_subscribe,
            can_publish_data=can_publish_data,
            expires_in_minutes=120,  # 2 hours
            metadata={
                "role": user_role,
                "user_id": user_id,
                "authenticated": current_user is not None,
                "permissions": {
                    "can_record": user_role == "physician",
                    "can_moderate": user_role == "physician",
                    "can_end_meeting": user_role == "physician"
                }
            }
        )
        
        # Calculate token expiration
        expires_at = datetime.utcnow() + timedelta(hours=2)
        
        # Log the join action
        logger.info("User joined meeting",
                   meeting_id=meeting_id,
                   user_id=user_id,
                   user_name=user_name,
                   user_role=user_role,
                   authenticated_user=current_user.id if current_user else None,
                   client_ip=http_request.client.host if http_request else None)
        
        return JoinMeetingResponse(
            token=token,
            meeting_id=meeting_id,
            user_name=user_name,
            livekit_url=settings.LIVEKIT_URL,
            user_id=user_id,
            success=True,
            expires_at=expires_at.isoformat(),
            permissions={
                "can_publish": can_publish,
                "can_subscribe": can_subscribe,
                "can_publish_data": can_publish_data,
                "is_admin": user_role == "physician"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to join meeting", 
                    error=str(e),
                    meeting_id=meeting_id,
                    user_name=request.user_name)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to join meeting: {str(e)}"
        )


@router.get("/{meeting_id}/info")
async def get_meeting_info(meeting_id: str) -> Dict[str, Any]:
    """
    Get meeting information without joining
    """
    try:
        room_info = await livekit_client.get_room_info(meeting_id)
        if not room_info:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        return {
            "meeting_id": meeting_id,
            "exists": True,
            "num_participants": room_info.get("num_participants", 0),
            "max_participants": room_info.get("max_participants", 10),
            "created_at": room_info.get("creation_time"),
            "is_full": room_info.get("num_participants", 0) >= room_info.get("max_participants", 10)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get meeting info", meeting_id=meeting_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get meeting information")


@router.get("/{meeting_id}/exists")
async def check_meeting_exists(meeting_id: str) -> Dict[str, bool]:
    """
    Simple endpoint to check if a meeting exists
    """
    try:
        exists = await livekit_client.room_exists(meeting_id)
        return {"exists": exists}
    except Exception as e:
        logger.error("Failed to check meeting existence", meeting_id=meeting_id, error=str(e))
        return {"exists": False}


@router.post("/{meeting_id}/validate-token")
async def validate_meeting_token(meeting_id: str, request: dict) -> Dict[str, Any]:
    """
    Validate a meeting token
    """
    try:
        token = request.get("token")
        if not token:
            raise HTTPException(status_code=400, detail="Token is required")
            
        validation_result = await livekit_client.validate_token(token)
        
        if not validation_result.get("valid"):
            raise HTTPException(status_code=401, detail=validation_result.get("error", "Invalid token"))
        
        # Check if token is for the correct room
        token_room = validation_result.get("room_name")
        if token_room != meeting_id:
            raise HTTPException(status_code=403, detail="Token not valid for this meeting")
        
        return validation_result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to validate token", meeting_id=meeting_id, error=str(e))
        raise HTTPException(status_code=500, detail="Token validation failed")


@router.delete("/{meeting_id}")
async def end_meeting(
    meeting_id: str,
    current_user: User = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    End a meeting (admin only)
    """
    try:
        # Only physicians or admins can end meetings
        if not current_user or not current_user.can_create_rooms:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        success = await livekit_client.delete_room(meeting_id)
        
        if success:
            logger.info("Meeting ended", meeting_id=meeting_id, ended_by=current_user.id)
            return {"success": True, "message": "Meeting ended successfully"}
        else:
            raise HTTPException(status_code=404, detail="Meeting not found or already ended")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to end meeting", meeting_id=meeting_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to end meeting")


@router.post("/{meeting_id}/start-recording")
async def start_recording(
    meeting_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Start recording a meeting (physicians only)
    """
    try:
        # Check if room exists
        room_info = await livekit_client.get_room_info(meeting_id)
        if not room_info:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # Only physicians can start recordings
        if not current_user or current_user.role.value != "physician":
            raise HTTPException(status_code=403, detail="Only physicians can start recordings")
        
        # Generate recording filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = f"recordings/{meeting_id}_{timestamp}.mp4"
        
        recording_id = await livekit_client.start_recording(meeting_id, output_file)
        
        if recording_id:
            logger.info("Recording started", 
                       meeting_id=meeting_id, 
                       recording_id=recording_id,
                       started_by=current_user.id)
            
            return {
                "success": True,
                "recording_id": recording_id,
                "output_file": output_file,
                "message": "Recording started successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to start recording")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start recording", meeting_id=meeting_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to start recording")


@router.post("/{meeting_id}/stop-recording")
async def stop_recording(
    meeting_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Stop recording a meeting (physicians only)
    """
    try:
        # Only physicians can stop recordings
        if not current_user or current_user.role.value != "physician":
            raise HTTPException(status_code=403, detail="Only physicians can stop recordings")
        
        # For simplicity, we'll use the meeting_id as recording_id
        # In a real implementation, you'd track active recordings
        success = await livekit_client.stop_recording(meeting_id)
        
        if success:
            logger.info("Recording stopped", 
                       meeting_id=meeting_id,
                       stopped_by=current_user.id)
            
            return {
                "success": True,
                "message": "Recording stopped successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="No active recording found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to stop recording", meeting_id=meeting_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to stop recording") 