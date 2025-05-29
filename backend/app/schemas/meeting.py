"""
Simple meeting schemas - Google Meet style
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.room import RoomStatus


class SimpleMeetingCreate(BaseModel):
    """Schema for creating an instant meeting"""
    name: Optional[str] = Field(None, description="Optional meeting name")


class SimpleMeetingResponse(BaseModel):
    """Response schema for meeting creation and info"""
    meeting_id: str = Field(..., description="Unique meeting ID (xxx-xxxx-xxx format)")
    meeting_url: str = Field(..., description="Full URL to join the meeting")
    created_at: datetime
    expires_at: datetime
    status: RoomStatus = RoomStatus.ACTIVE
    
    class Config:
        orm_mode = True


class SimpleMeetingJoin(BaseModel):
    """Schema for joining a meeting"""
    display_name: str = Field(..., min_length=1, max_length=50, description="Display name for the participant")


class SimpleMeetingTokenResponse(BaseModel):
    """Response schema for meeting join token"""
    token: str = Field(..., description="LiveKit access token")
    meeting_id: str
    livekit_url: str
    participant_id: str 