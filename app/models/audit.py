"""
Audit log model for HIPAA compliance
"""

from typing import Optional

from sqlalchemy import Boolean, Column, Enum, ForeignKey, String, JSON, Text
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class AuditAction(str, enum.Enum):
    """
    Audit action types
    """
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    JOIN = "join"
    LEAVE = "leave"
    START_RECORDING = "start_recording"
    STOP_RECORDING = "stop_recording"


class AuditLog(BaseModel):
    """
    Audit log model for HIPAA compliance
    Stores all access and modification events
    """
    __tablename__ = "audit_logs"
    
    # User who performed the action
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Action performed
    action = Column(Enum(AuditAction), nullable=False, index=True)
    
    # Resource type (e.g., 'room', 'user', 'recording')
    resource_type = Column(String(50), nullable=False, index=True)
    
    # Resource ID
    resource_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Request details
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(255), nullable=True)
    
    # Result
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Additional metadata
    metadata = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    user = relationship(
        "User",
        back_populates="audit_logs"
    )
    
    @property
    def is_sensitive_action(self) -> bool:
        """Check if this is a sensitive action requiring special handling"""
        sensitive_actions = [
            AuditAction.DELETE,
            AuditAction.START_RECORDING,
            AuditAction.STOP_RECORDING
        ]
        return self.action in sensitive_actions
    
    @property
    def is_failed(self) -> bool:
        """Check if action failed"""
        return not self.success
    
    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, user_id={self.user_id}, "
            f"action={self.action.value}, resource={self.resource_type})>"
        ) 