"""
Meeting link model for secure access tokens
"""

from typing import Optional
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class MeetingLink(BaseModel):
    """
    Meeting link model for secure room access
    """
    __tablename__ = "meeting_links"
    __table_args__ = (
        UniqueConstraint('room_id', 'user_id', name='_room_user_link_uc'),
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
    
    # Unique token
    token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Expiration
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    
    # Usage limits
    max_uses = Column(Integer, default=1, nullable=False)
    use_count = Column(Integer, default=0, nullable=False)
    
    # Last used
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    room = relationship(
        "Room",
        back_populates="meeting_links"
    )
    
    user = relationship(
        "User",
        back_populates="meeting_links"
    )
    
    @property
    def is_expired(self) -> bool:
        """Check if link is expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_exhausted(self) -> bool:
        """Check if link has reached max uses"""
        return self.use_count >= self.max_uses
    
    @property
    def is_valid(self) -> bool:
        """Check if link is still valid"""
        return not self.is_expired and not self.is_exhausted
    
    @property
    def remaining_uses(self) -> int:
        """Get remaining uses"""
        return max(0, self.max_uses - self.use_count)
    
    def use(self) -> bool:
        """
        Use the link if valid
        Returns True if successful, False otherwise
        """
        if not self.is_valid:
            return False
        
        self.use_count += 1
        self.last_used_at = datetime.utcnow()
        return True
    
    def extend_expiration(self, hours: int = 24) -> None:
        """Extend link expiration"""
        from datetime import timedelta
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
    
    def __repr__(self) -> str:
        return (
            f"<MeetingLink(id={self.id}, room_id={self.room_id}, "
            f"user_id={self.user_id}, is_valid={self.is_valid})>"
        ) 