"""
Recording schemas for API validation
"""

from typing import List, Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.recording import RecordingStatus


class RecordingBase(BaseModel):
    """Base recording schema"""
    room_id: UUID
    metadata: dict = Field(default_factory=dict)


class StartRecordingRequest(BaseModel):
    """Schema for starting a recording"""
    room_id: UUID
    audio_only: bool = False
    consent_given: bool = False


class RecordingConsentRequest(BaseModel):
    """Schema for recording consent"""
    consent_given: bool


class RecordingResponse(RecordingBase):
    """Schema for recording response"""
    id: UUID
    recording_id: str
    status: RecordingStatus
    started_by: Optional[UUID]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    file_size_bytes: Optional[int]
    consent_given: bool
    consent_given_by: List[UUID]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True


class RecordingListResponse(BaseModel):
    """Schema for recording list response"""
    recordings: List[RecordingResponse]
    total: int
    page: int
    page_size: int 