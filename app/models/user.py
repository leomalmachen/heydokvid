"""
User model with encryption for sensitive data
"""

from typing import List, Optional
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, String, JSON
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    """
    User roles enumeration
    """
    PHYSICIAN = "physician"
    PATIENT = "patient"
    ADMIN = "admin"
    OBSERVER = "observer"


class User(BaseModel):
    """
    User model for authentication and authorization
    """
    __tablename__ = "users"
    
    # External ID from heydok system
    external_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Email (unique identifier)
    email = Column(String(255), unique=True, nullable=False, index=True)
    
    # Role
    role = Column(Enum(UserRole), nullable=False)
    
    # Encrypted name for GDPR compliance
    encrypted_name = Column(String, nullable=False)
    
    # Activity tracking
    last_login = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Additional metadata
    metadata = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    created_rooms = relationship(
        "Room",
        back_populates="creator",
        foreign_keys="Room.created_by"
    )
    
    participations = relationship(
        "Participant",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    audit_logs = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    meeting_links = relationship(
        "MeetingLink",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    sent_messages = relationship(
        "ChatMessage",
        back_populates="sender",
        foreign_keys="ChatMessage.sender_id"
    )
    
    started_recordings = relationship(
        "Recording",
        back_populates="started_by_user",
        foreign_keys="Recording.started_by"
    )
    
    @property
    def is_physician(self) -> bool:
        """Check if user is a physician"""
        return self.role == UserRole.PHYSICIAN
    
    @property
    def is_patient(self) -> bool:
        """Check if user is a patient"""
        return self.role == UserRole.PATIENT
    
    @property
    def is_admin(self) -> bool:
        """Check if user is an admin"""
        return self.role == UserRole.ADMIN
    
    @property
    def can_create_rooms(self) -> bool:
        """Check if user can create rooms"""
        return self.role in [UserRole.PHYSICIAN, UserRole.ADMIN]
    
    @property
    def can_record(self) -> bool:
        """Check if user can start recordings"""
        return self.role in [UserRole.PHYSICIAN, UserRole.ADMIN]
    
    def update_last_login(self) -> None:
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role.value})>" 