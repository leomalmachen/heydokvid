"""
Recording model for encrypted video recordings
"""

from typing import List, Optional
from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, JSON, Text, BigInteger
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class RecordingStatus(str, enum.Enum):
    """
    Recording status enumeration
    """
    PENDING = "pending"
    RECORDING = "recording"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Recording(BaseModel):
    """
    Recording model for storing encrypted recordings
    """
    __tablename__ = "recordings"
    
    # Room reference
    room_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # LiveKit recording ID
    recording_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Status
    status = Column(
        Enum(RecordingStatus),
        nullable=False,
        default=RecordingStatus.PENDING,
        index=True
    )
    
    # Started by
    started_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Duration in seconds
    duration_seconds = Column(Integer, nullable=True)
    
    # File information
    file_size_bytes = Column(BigInteger, nullable=True)
    encrypted_file_path = Column(Text, nullable=True)  # Encrypted path
    encryption_key_id = Column(String(255), nullable=True)  # Key ID for decryption
    
    # Consent tracking
    consent_given = Column(Boolean, default=False, nullable=False)
    consent_given_by = Column(
        ARRAY(PGUUID(as_uuid=True)),
        default=list,
        nullable=False
    )
    
    # Soft delete for GDPR
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Additional metadata
    metadata = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    room = relationship(
        "Room",
        back_populates="recordings"
    )
    
    started_by_user = relationship(
        "User",
        back_populates="started_recordings",
        foreign_keys=[started_by]
    )
    
    @property
    def is_active(self) -> bool:
        """Check if recording is currently active"""
        return self.status == RecordingStatus.RECORDING
    
    @property
    def is_completed(self) -> bool:
        """Check if recording is completed"""
        return self.status == RecordingStatus.COMPLETED
    
    @property
    def is_deleted(self) -> bool:
        """Check if recording is soft deleted"""
        return self.deleted_at is not None
    
    @property
    def has_consent(self) -> bool:
        """Check if consent was given"""
        return self.consent_given and len(self.consent_given_by) > 0
    
    @property
    def file_size_mb(self) -> Optional[float]:
        """Get file size in MB"""
        if self.file_size_bytes:
            return round(self.file_size_bytes / (1024 * 1024), 2)
        return None
    
    def start(self) -> None:
        """Mark recording as started"""
        self.status = RecordingStatus.RECORDING
        self.started_at = datetime.utcnow()
    
    def stop(self) -> None:
        """Mark recording as stopped"""
        self.status = RecordingStatus.PROCESSING
        self.ended_at = datetime.utcnow()
        if self.started_at:
            self.duration_seconds = int((self.ended_at - self.started_at).total_seconds())
    
    def complete(self, file_path: str, file_size: int, encryption_key_id: str) -> None:
        """Mark recording as completed"""
        self.status = RecordingStatus.COMPLETED
        self.encrypted_file_path = file_path
        self.file_size_bytes = file_size
        self.encryption_key_id = encryption_key_id
    
    def fail(self, error_message: str) -> None:
        """Mark recording as failed"""
        self.status = RecordingStatus.FAILED
        self.metadata["error_message"] = error_message
    
    def add_consent(self, user_id: UUID) -> None:
        """Add user consent"""
        if user_id not in self.consent_given_by:
            self.consent_given_by = self.consent_given_by + [user_id]
            self.consent_given = True
    
    def soft_delete(self) -> None:
        """Soft delete recording for GDPR compliance"""
        self.deleted_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        return (
            f"<Recording(id={self.id}, room_id={self.room_id}, "
            f"status={self.status.value}, has_consent={self.has_consent})>"
        ) 