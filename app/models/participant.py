"""
Participant model for room participants
"""

from typing import Optional
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, JSON, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel
from app.models.user import UserRole


class ParticipantStatus(str, enum.Enum):
    """
    Participant status enumeration
    """
    INVITED = "invited"
    JOINED = "joined"
    LEFT = "left"
    DISCONNECTED = "disconnected"


class Participant(BaseModel):
    """
    Participant model for tracking room participants
    """
    __tablename__ = "participants"
    __table_args__ = (
        UniqueConstraint('room_id', 'user_id', name='_room_user_uc'),
    )
    
    # Room reference
    room_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # User reference
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # LiveKit participant ID
    participant_id = Column(String(255), nullable=False)
    
    # Status
    status = Column(
        Enum(ParticipantStatus),
        nullable=False,
        default=ParticipantStatus.INVITED
    )
    
    # Role in this room
    role = Column(Enum(UserRole), nullable=False)
    
    # Encrypted join token
    join_token = Column(Text, nullable=True)
    
    # Timestamps
    joined_at = Column(DateTime(timezone=True), nullable=True)
    left_at = Column(DateTime(timezone=True), nullable=True)
    
    # Duration in seconds
    duration_seconds = Column(Integer, nullable=True)
    
    # Permissions
    is_presenter = Column(Boolean, default=False, nullable=False)
    can_publish = Column(Boolean, default=True, nullable=False)
    can_subscribe = Column(Boolean, default=True, nullable=False)
    
    # Additional metadata
    metadata = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    room = relationship(
        "Room",
        back_populates="participants"
    )
    
    user = relationship(
        "User",
        back_populates="participations"
    )
    
    @property
    def is_active(self) -> bool:
        """Check if participant is currently active"""
        return self.status == ParticipantStatus.JOINED
    
    @property
    def has_joined(self) -> bool:
        """Check if participant has ever joined"""
        return self.joined_at is not None
    
    @property
    def connection_duration(self) -> Optional[int]:
        """Calculate connection duration in seconds"""
        if self.joined_at:
            end_time = self.left_at or datetime.utcnow()
            return int((end_time - self.joined_at).total_seconds())
        return None
    
    def join(self) -> None:
        """Mark participant as joined"""
        self.status = ParticipantStatus.JOINED
        self.joined_at = datetime.utcnow()
    
    def leave(self) -> None:
        """Mark participant as left"""
        self.status = ParticipantStatus.LEFT
        self.left_at = datetime.utcnow()
        self.duration_seconds = self.connection_duration
    
    def disconnect(self) -> None:
        """Mark participant as disconnected"""
        self.status = ParticipantStatus.DISCONNECTED
        self.left_at = datetime.utcnow()
        self.duration_seconds = self.connection_duration
    
    def __repr__(self) -> str:
        return (
            f"<Participant(id={self.id}, room_id={self.room_id}, "
            f"user_id={self.user_id}, status={self.status.value})>"
        ) 