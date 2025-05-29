"""
Chat message model for encrypted messages
"""

from typing import Optional
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, JSON, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ChatMessage(BaseModel):
    """
    Chat message model for encrypted in-call messages
    """
    __tablename__ = "chat_messages"
    
    # Room reference
    room_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Sender reference
    sender_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Encrypted message content
    encrypted_message = Column(Text, nullable=False)
    
    # Timestamps
    sent_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    edited_at = Column(DateTime(timezone=True), nullable=True)
    
    # Soft delete for message retraction
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Additional metadata
    metadata = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    room = relationship(
        "Room",
        back_populates="chat_messages"
    )
    
    sender = relationship(
        "User",
        back_populates="sent_messages",
        foreign_keys=[sender_id]
    )
    
    @property
    def is_deleted(self) -> bool:
        """Check if message is deleted"""
        return self.deleted_at is not None
    
    @property
    def is_edited(self) -> bool:
        """Check if message was edited"""
        return self.edited_at is not None
    
    @property
    def is_system_message(self) -> bool:
        """Check if this is a system message"""
        return self.sender_id is None
    
    def edit(self, new_encrypted_message: str) -> None:
        """Edit message content"""
        self.encrypted_message = new_encrypted_message
        self.edited_at = datetime.utcnow()
    
    def soft_delete(self) -> None:
        """Soft delete message"""
        self.deleted_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        return (
            f"<ChatMessage(id={self.id}, room_id={self.room_id}, "
            f"sender_id={self.sender_id}, is_deleted={self.is_deleted})>"
        ) 