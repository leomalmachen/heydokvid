"""
Room model for video conference rooms
"""

from typing import List, Optional
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class RoomStatus(str, enum.Enum):
    """
    Room status enumeration
    """
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    ENDED = "ended"
    CANCELLED = "cancelled"


class Room(BaseModel):
    """
    Room model for video conferences
    """
    __tablename__ = "rooms"
    
    # LiveKit room ID
    room_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Room name
    name = Column(String(255), nullable=False)
    
    # Status
    status = Column(
        Enum(RoomStatus),
        nullable=False,
        default=RoomStatus.SCHEDULED,
        index=True
    )
    
    # Creator
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True  # Allow anonymous meetings
    )
    
    # Scheduling
    scheduled_start = Column(DateTime(timezone=True), nullable=True, index=True)
    scheduled_end = Column(DateTime(timezone=True), nullable=True)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    actual_end = Column(DateTime(timezone=True), nullable=True)
    
    # Settings
    max_participants = Column(Integer, default=20, nullable=False)
    enable_recording = Column(Boolean, default=False, nullable=False)
    enable_chat = Column(Boolean, default=True, nullable=False)
    enable_screen_share = Column(Boolean, default=True, nullable=False)
    waiting_room_enabled = Column(Boolean, default=True, nullable=False)
    
    # Additional metadata
    metadata = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    creator = relationship(
        "User",
        back_populates="created_rooms",
        foreign_keys=[created_by]
    )
    
    participants = relationship(
        "Participant",
        back_populates="room",
        cascade="all, delete-orphan"
    )
    
    recordings = relationship(
        "Recording",
        back_populates="room",
        cascade="all, delete-orphan"
    )
    
    chat_messages = relationship(
        "ChatMessage",
        back_populates="room",
        cascade="all, delete-orphan"
    )
    
    meeting_links = relationship(
        "MeetingLink",
        back_populates="room",
        cascade="all, delete-orphan"
    )
    
    @property
    def is_active(self) -> bool:
        """Check if room is currently active"""
        return self.status == RoomStatus.ACTIVE
    
    @property
    def is_scheduled(self) -> bool:
        """Check if room is scheduled"""
        return self.status == RoomStatus.SCHEDULED
    
    @property
    def is_ended(self) -> bool:
        """Check if room has ended"""
        return self.status == RoomStatus.ENDED
    
    @property
    def duration_seconds(self) -> Optional[int]:
        """Calculate room duration in seconds"""
        if self.actual_start and self.actual_end:
            return int((self.actual_end - self.actual_start).total_seconds())
        return None
    
    @property
    def participant_count(self) -> int:
        """Get current participant count"""
        return len([p for p in self.participants if p.status == "joined"])
    
    def start(self) -> None:
        """Mark room as started"""
        self.status = RoomStatus.ACTIVE
        self.actual_start = datetime.utcnow()
    
    def end(self) -> None:
        """Mark room as ended"""
        self.status = RoomStatus.ENDED
        self.actual_end = datetime.utcnow()
    
    def cancel(self) -> None:
        """Cancel room"""
        self.status = RoomStatus.CANCELLED
    
    def __repr__(self) -> str:
        return f"<Room(id={self.id}, room_id={self.room_id}, status={self.status.value})>" 