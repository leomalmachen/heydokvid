"""
Chat schemas for API validation
"""

from typing import List, Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, validator


class ChatMessageBase(BaseModel):
    """Base chat message schema"""
    message: str = Field(..., min_length=1, max_length=1000)
    metadata: dict = Field(default_factory=dict)


class ChatMessageCreate(ChatMessageBase):
    """Schema for creating a chat message"""
    
    @validator('message')
    def validate_message(cls, v):
        # Basic message validation
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()


class ChatMessageUpdate(BaseModel):
    """Schema for updating a chat message"""
    message: Optional[str] = Field(None, min_length=1, max_length=1000)


class ChatMessageResponse(BaseModel):
    """Schema for chat message response"""
    id: UUID
    room_id: UUID
    sender_id: Optional[UUID]
    message: str  # Decrypted message
    sent_at: datetime
    edited_at: Optional[datetime]
    metadata: dict
    
    class Config:
        orm_mode = True


class ChatMessageListResponse(BaseModel):
    """Schema for chat message list response"""
    messages: List[ChatMessageResponse]
    total: int
    page: int
    page_size: int 