"""
Room schemas for API validation
"""

from typing import List, Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.models.room import RoomStatus


class RoomBase(BaseModel):
    """Base room schema"""
    name: str = Field(..., min_length=1, max_length=255)
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    max_participants: int = Field(20, ge=2, le=100)
    enable_recording: bool = False
    enable_chat: bool = True
    enable_screen_share: bool = True
    waiting_room_enabled: bool = True
    metadata: dict = Field(default_factory=dict)


class RoomCreate(RoomBase):
    """Schema for creating a room"""
    
    @validator('scheduled_end')
    def validate_scheduled_end(cls, v, values):
        if v and 'scheduled_start' in values and values['scheduled_start']:
            if v <= values['scheduled_start']:
                raise ValueError('scheduled_end must be after scheduled_start')
        return v


class RoomUpdate(BaseModel):
    """Schema for updating a room"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    max_participants: Optional[int] = Field(None, ge=2, le=100)
    enable_recording: Optional[bool] = None
    enable_chat: Optional[bool] = None
    enable_screen_share: Optional[bool] = None
    waiting_room_enabled: Optional[bool] = None
    metadata: Optional[dict] = None


class RoomResponse(RoomBase):
    """Schema for room response"""
    id: UUID
    room_id: str
    status: RoomStatus
    created_by: Optional[UUID]
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    participant_count: int = 0
    
    class Config:
        orm_mode = True
        from_attributes = True


class RoomListResponse(BaseModel):
    """Schema for room list response"""
    rooms: List[RoomResponse]
    total: int
    page: int
    page_size: int


class RoomTokenRequest(BaseModel):
    """Schema for requesting room access token"""
    room_id: str = Field(..., min_length=1)
    user_name: Optional[str] = None


class RoomTokenResponse(BaseModel):
    """Schema for room token response"""
    token: str
    room_id: str
    livekit_url: str
    expires_at: datetime


class CreateMeetingLinkRequest(BaseModel):
    """Schema for creating meeting links"""
    physician_id: UUID
    patient_id: UUID
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    enable_recording: bool = False


class CreateMeetingLinkResponse(BaseModel):
    """Schema for meeting link response"""
    room_id: str
    physician_link: str
    patient_link: str
    expires_at: datetime 