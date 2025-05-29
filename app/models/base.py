"""
Base model with common fields
"""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
import uuid

from app.core.database import Base


class BaseModel(Base):
    """
    Abstract base model with common fields
    """
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generate table name from class name
        """
        # Convert CamelCase to snake_case
        name = cls.__name__
        return ''.join(['_' + c.lower() if c.isupper() else c for c in name]).lstrip('_')
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def __repr__(self) -> str:
        """
        String representation
        """
        return f"<{self.__class__.__name__}(id={self.id})>" 